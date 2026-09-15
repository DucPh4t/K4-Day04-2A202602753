from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

# Nạp biến môi trường từ starter_v0/.env nếu có
load_lab_env(ROOT)
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="IT Helpdesk Agent — Interactive UI",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "transcript_id" not in st.session_state:
    st.session_state.transcript_id = None
if "turn_index" not in st.session_state:
    st.session_state.turn_index = 0

# --- SIDEBAR: Cấu hình hệ thống & Metadata ---
with st.sidebar:
    st.title("⚙️ Cấu hình Agent")

    # Tự động chọn Provider đã có API Key trong môi trường
    provider_options = ["openai", "openrouter", "gemini", "anthropic"]
    default_index = 0
    if os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        default_index = provider_options.index("openai")
    elif os.getenv("OPENROUTER_API_KEY"):
        default_index = provider_options.index("openrouter")
    elif os.getenv("GEMINI_API_KEY"):
        default_index = provider_options.index("gemini")
    elif os.getenv("ANTHROPIC_API_KEY"):
        default_index = provider_options.index("anthropic")

    provider_name = st.selectbox(
        "Model Provider",
        options=provider_options,
        index=default_index,
        help="Chọn nhà cung cấp mô hình AI hỗ trợ Structured Tool Calling.",
    )

    custom_model = st.text_input(
        "Model ID (Tùy chọn)",
        value="",
        placeholder="Để trống để dùng model mặc định",
        help="Ví dụ: openai/gpt-4o, google/gemini-2.5-flash,...",
    )

    # Khung nhập API Key trực tiếp nếu chưa cấu hình .env
    key_env_var = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider_name, "API_KEY")

    has_env_key = bool(os.getenv(key_env_var))
    key_placeholder = f"Đã cấu hình trong .env ({key_env_var})" if has_env_key else f"Nhập {key_env_var}"
    override_api_key = st.text_input(
        f"API Key ({provider_name.title()})",
        type="password",
        placeholder=key_placeholder,
        help="Bạn có thể cấu hình trong file starter_v0/.env hoặc nhập trực tiếp tại đây.",
    )

    if override_api_key:
        os.environ[key_env_var] = override_api_key.strip()
    elif not has_env_key:
        st.warning(f"⚠️ Chưa có API key cho **{provider_name}**. Vui lòng nhập vào ô trên hoặc cấu hình trong file `starter_v0/.env`.")

    st.markdown("---")
    st.subheader("📦 Phiên bản & Artifacts")
    version_label = st.text_input("Artifact Version", value="v3", help="Nhãn phiên bản (v0, v1, v2, v3).")

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"

    try:
        artifact_ver = build_artifact_version(version_label, system_prompt_path, tools_path)
        st.success(f"**Version**: `{artifact_ver.artifact_version}`")
        with st.expander("🔍 Chi tiết mã băm SHA256"):
            st.code(
                f"Prompt Hash: {artifact_ver.prompt_hash[:12]}...\n"
                f"Tools Hash:  {artifact_ver.tools_hash[:12]}...",
                language="text",
            )
    except Exception as e:
        st.warning(f"Lỗi tính toán hash: {e}")
        artifact_ver = None

    history_window = st.slider(
        "Ngữ cảnh nhớ (History Window)",
        min_value=1,
        max_value=10,
        value=5,
        help="Số lượt hỏi-đáp gần nhất được đưa vào ngữ cảnh.",
    )

    max_tool_rounds = st.slider(
        "Số vòng gọi tool tối đa",
        min_value=1,
        max_value=8,
        value=4,
        help="Giới hạn số vòng Agent được phép gọi tool liên tiếp trong một lượt.",
    )

    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.transcript_id = None
        st.session_state.turn_index = 0
        st.rerun()

    with st.expander(f"🛠️ Danh sách Tool ({len(TOOL_FUNCTIONS)})"):
        for name in sorted(TOOL_FUNCTIONS.keys()):
            st.markdown(f"- `{name}`")


# --- MAIN CHAT AREA ---
st.title("🛠️ IT Helpdesk Agent — Live Chat")
st.caption(
    "Hệ thống trợ lý kỹ thuật IT Helpdesk với khả năng định tuyến công cụ, kiểm soát ranh giới an toàn, "
    "xác nhận trước khi ghi và minh bạch toàn bộ vết thực thi Tool Calling."
)

# Tải tài nguyên hệ thống
@st.cache_data(show_spinner=False)
def get_system_prompt() -> str:
    return system_prompt_path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def get_openai_tools() -> list[dict[str, Any]]:
    decls = load_tool_declarations(tools_path)
    return to_openai_tools(decls)


try:
    system_prompt = get_system_prompt()
    openai_tools = get_openai_tools()
except Exception as e:
    st.error(f"Không thể đọc file prompt hoặc tools: {e}")
    st.stop()

# Khởi tạo transcript session nếu chưa có
if st.session_state.transcript_id is None:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.transcript_id = "_".join([
        safe_slug(version_label),
        safe_slug(provider_name),
        timestamp,
    ])

transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"

# Gợi ý câu hỏi mẫu nếu chưa có tin nhắn
if not st.session_state.messages:
    st.markdown("##### 💡 Câu hỏi mẫu để thử nghiệm nhanh:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌐 Kiểm tra VPN production", use_container_width=True):
            st.session_state.pending_prompt = "Dịch vụ VPN production hiện tại có đang gặp sự cố gián đoạn không?"
            st.rerun()
    with col2:
        if st.button("💻 Chẩn đoán máy LT-204", use_container_width=True):
            st.session_state.pending_prompt = "Máy tính của tôi mã tài sản LT-204 bị mất mạng, kiểm tra giúp tôi."
            st.rerun()
    with col3:
        if st.button("📦 Kiểm tra Docker Desktop", use_container_width=True):
            st.session_state.pending_prompt = "Phần mềm Docker Desktop có được phép sử dụng trong công ty không?"
            st.rerun()

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Nếu là assistant và có tool trace, hiển thị chi tiết
        if msg["role"] == "assistant" and msg.get("tool_events"):
            events = msg["tool_events"]
            status_text = msg.get("status", "completed")
            with st.expander(f"🔍 Chi tiết Tool Calling ({len(events)} lượt gọi, status: {status_text})", expanded=False):
                for i, event in enumerate(events, 1):
                    st.markdown(f"**Bước {i}: Gọi tool `{event.get('tool')}`**")
                    col_args, col_res = st.columns(2)
                    with col_args:
                        st.markdown("*Tham số đầu vào (Arguments):*")
                        st.json(event.get("args", {}))
                    with col_res:
                        res = event.get("result", {})
                        if isinstance(res, dict) and res.get("error"):
                            st.markdown("⚠️ *Kết quả (Lỗi):*")
                        else:
                            st.markdown("✅ *Kết quả trả về (Result):*")
                        st.json(res)
                    st.markdown("---")

        st.markdown(msg["content"])


# Xử lý input từ người dùng
user_input = st.chat_input("Nhập câu hỏi hoặc yêu cầu hỗ trợ kỹ thuật...")
if getattr(st.session_state, "pending_prompt", None):
    user_input = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if user_input:
    # 1. Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Chuẩn bị ngữ cảnh hội thoại
    st.session_state.turn_index += 1
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_input},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_input,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    # 3. Chạy Agent Tool Loop
    with st.chat_message("assistant"):
        with st.spinner("Đang suy luận và thực thi công cụ..."):
            try:
                provider = make_provider(provider_name)
                selected_model = custom_model.strip() or None

                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )

                turn_record.update(result)
                assistant_text = result.get("assistant_text", "")
                tool_events = result.get("tool_events", [])
                status = result.get("status", "answered")

                # Hiển thị Tool Call Trace ngay lập tức
                if tool_events:
                    with st.expander(f"🔍 Chi tiết Tool Calling ({len(tool_events)} lượt gọi, status: {status})", expanded=True):
                        for i, event in enumerate(tool_events, 1):
                            st.markdown(f"**Bước {i}: Gọi tool `{event.get('tool')}`**")
                            col_args, col_res = st.columns(2)
                            with col_args:
                                st.markdown("*Tham số đầu vào (Arguments):*")
                                st.json(event.get("args", {}))
                            with col_res:
                                res = event.get("result", {})
                                if isinstance(res, dict) and res.get("error"):
                                    st.markdown("⚠️ *Kết quả (Lỗi):*")
                                else:
                                    st.markdown("✅ *Kết quả trả về (Result):*")
                                st.json(res)
                            st.markdown("---")

                st.markdown(assistant_text)

                # Lưu vào bộ nhớ hội thoại
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "tool_events": tool_events,
                    "status": status,
                })
                st.session_state.history.append({"role": "user", "content": user_input})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})

            except Exception as exc:
                err_msg = f"{type(exc).__name__}: {str(exc)}"
                turn_record.update({"status": "provider_error", "error": err_msg})
                st.error(
                    f"❌ **Lỗi thực thi Agent:** `{err_msg}`\n\n"
                    f"*Gợi ý:* Hãy kiểm tra lại API Key của provider `{provider_name}` trong thanh Sidebar hoặc file `starter_v0/.env`."
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"*(Lỗi hệ thống)*: Không thể kết nối với mô hình {provider_name}.",
                    "tool_events": [],
                    "status": "error",
                })

            turn_record["ended_at"] = now_iso()

    # 4. Ghi Transcript
    transcript_data: dict[str, Any] = {
        "transcript_id": st.session_state.transcript_id,
        **(artifact_version_dict(artifact_ver) if artifact_ver else {}),
        "provider": provider_name,
        "model": custom_model.strip() or getattr(provider, "default_model", None),
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [turn_record],
    }

    try:
        write_transcript(transcript_path, transcript_data)
        st.caption(f"📝 *Vết hội thoại được lưu tại:* `{transcript_path}`")
    except Exception as e:
        st.caption(f"⚠️ *Không thể lưu transcript:* {e}")
