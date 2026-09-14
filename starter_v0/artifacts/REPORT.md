# Day 04 Lab v3 Report — IT Helpdesk Agent

## Team

- Team:
- Members: Chử Trần Phương Nam
- Provider/model:

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Viết 1–2 câu mô tả capability và giới hạn của agent.

**Link dùng thử:**

> URL:

## A2. Tool agent có

| Tool | Chức năng | Core / optional / team-built |
|---|---|---|
| clarify | Hỏi bổ sung thông tin còn thiếu (asset ID, employee ID) hoặc xin xác nhận (confirmation) trước khi thực hiện hành động nhạy cảm | core |
| search_kb | Tìm kiếm hướng dẫn kỹ thuật, tài liệu khắc phục sự cố (how-to, troubleshooting) trong Knowledge Base nội bộ | core |
| check_service_status | Kiểm tra trạng thái hoạt động (health/outage) của các dịch vụ dùng chung toàn công ty (VPN, Email, SSO, Wi-Fi, Printing) | core |
| inspect_device | Tra cứu cấu hình và bản chụp chẩn đoán kỹ thuật (diagnostic snapshot) của một thiết bị cụ thể theo mã tài sản (asset ID) | core |
| lookup_user | Tra cứu thông tin nhân sự trong danh bạ IT và danh sách thiết bị được cấp phát theo mã nhân viên (Employee ID) | core |
| format_incident_report | Định dạng và tổng hợp các phát hiện kỹ thuật đã có thành báo cáo sự cố chuẩn Markdown | core |
| policy | Tra cứu quy định, tiêu chuẩn và chính sách IT nội bộ công ty (truy cập, bảo mật dữ liệu, quy trình ticket,...) | optional (built-in) |
| create_ticket | Tạo ticket hỗ trợ kỹ thuật trên hệ thống quản lý sự cố nội bộ (chỉ ghi khi đã được người dùng xác nhận) | optional (built-in) |
| search_device_info | Tìm kiếm thông số kỹ thuật, driver hoặc trang hỗ trợ công khai của nhà sản xuất thiết bị trên Web qua Tavily Search | optional (built-in) |

## A3. Câu hỏi mẫu

1.
2.
3.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

# PHẦN B — Chi tiết và evidence

Metric chỉ hợp lệ khi `provider_error_cases == 0`, `measured_cases ==
total_cases`, và tool result error đã được review thủ công.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run file |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

| Case ID | Failure type | Actual calls | What failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

Liệt kê đúng 10 case tự viết: 5 single-turn và 5 multi-turn.

| Case ID | What it tests | Expected behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

| Scenario/turn | Version | Tool calls + args | Transcript/run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B4a. Adversarial evidence

Phân tích ít nhất 3 cases. Automatic score không chứng minh rằng không có dữ
liệu bị ghi hoặc gửi ra ngoài; cần kiểm tra cả `tool_results` và filesystem.

| Attack case | Expected boundary | Actual calls | Sensitive write/exfiltration occurred? | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Optional và bonus tool evidence

Phần này chỉ điền khi nhóm có sử dụng optional tool hoặc tự xây bonus tool.
Không làm phần này không ảnh hưởng việc hoàn thành core lab. `policy`,
`create_ticket` và `search_device_info` là tool có sẵn, không phải tool mới do
nhóm tự xây.

| Category | Evidence file | What worked | Risk / guardrail |
|---|---|---|---|
| Optional built-in | `data/eval_helpdesk_extension.json` | `policy` tra cứu đúng chính sách nội bộ; `create_ticket` tạo ticket khi có xác nhận | Cấm ghi file nếu `confirmed: false`; từ chối summary chứa credentials/MFA |
| External search + privacy boundary | `data/eval_helpdesk_extension.json` | `search_device_info` tìm kiếm thông số và driver công khai thành công qua Tavily API | Chặn đứng rò rỉ dữ liệu: Báo lỗi ngay nếu query chứa mã asset ID, employee ID hoặc hostname nội bộ |
| Bonus: tool mới do nhóm tự xây | Không áp dụng (Nhóm tập trung tối ưu core và optional built-in) | Không áp dụng | Không áp dụng |

## B6. Safety review

- Agent có bao giờ tự đoán asset ID hoặc employee ID không?
- Trace/ticket có chứa password, MFA code, token hay dữ liệu thật không?
- Ticket chỉ được tạo sau xác nhận rõ chưa?
- Tool result error nào cần review thủ công?

## B7. Technical reflection

- Fix nào thuộc `system_prompt.md`?
- **Fix thuộc `tools.yaml`:**
  - Chuẩn hóa mô tả ranh giới phân định giữa dịch vụ dùng chung toàn công ty (`check_service_status`) và kiểm tra một tài sản cụ thể (`inspect_device`).
  - Khai báo danh sách enum tường minh cho các trường tham số: `check`, `service`, `environment`, `category`, `policy_area`, `query_type`, `template`.
  - Cài đặt ranh giới an toàn: Yêu cầu `confirmed: true` và cảnh báo không chứa secret trong `create_ticket`; nghiêm cấm truyền asset ID, employee ID hoặc hostname nội bộ ra ngoài web trong `search_device_info`.
- Failure nào không thể chỉ nhìn automatic score?
- Nếu có thêm một vòng, nhóm sẽ thử hypothesis nào?

# PHẦN C — Checkout trước khi nộp

Phần này được hoàn thành sau khi toàn bộ code, evidence và report đã được đưa
lên repository chung. Nhóm chưa nên nộp link trên VLearn nếu reflection hoặc
commit evidence của bất kỳ thành viên nào còn thiếu.

## C1. Reflection chung của nhóm

Các thành viên thảo luận và viết một reflection chung. Nội dung cần dựa trên
evidence thực tế trong repository, không chỉ mô tả cảm nhận chung.

- Mục tiêu nào của nhóm đã hoàn thành? Dẫn đến artifact hoặc run tương ứng.
- Hypothesis hoặc thay đổi nào tạo ra cải thiện rõ nhất?
- Failure quan trọng nào vẫn chưa xử lý được hoàn toàn?
- Nhóm đã phân chia, review và tích hợp công việc như thế nào?
- Nếu có thêm một vòng, nhóm sẽ ưu tiên thay đổi và kiểm chứng điều gì?

**Reflection chung của nhóm:**

> Viết reflection tại đây và dẫn link/path đến evidence liên quan.

## C2. Self-reflection của từng thành viên

Mỗi thành viên tự viết một mục riêng về phần việc chính mình đã thực hiện trong
repository chung. Không viết thay hoặc gộp nhiều thành viên vào một câu trả lời.
Mỗi reflection cần trỏ đến file, commit hoặc pull request có thật để người đọc
có thể đối chiếu đóng góp.

Sao chép mẫu dưới đây cho từng thành viên:

### Chử Trần Phương Nam — 2A202602675

- **Vai trò/phần việc được nhận:** Tool & Schema Engineer (Người 2)
- **Những gì tôi đã thay đổi trong repo chung:** Chuẩn hóa toàn bộ 9 tools trong tools.yaml (làm rõ mô tả ranh giới capabilities, bổ sung đầy đủ enum cho các tham số check, service, environment, policy_area, query_type; siết ranh giới bảo mật cho create_ticket và search_device_info); hoàn thành Mục A2 (Bảng 9 tools) trong REPORT.md.
- **File hoặc artifact liên quan:** `starter_v0/artifacts/tools.yaml`, `starter_v0/artifacts/REPORT.md`
- **Commit hash hoặc pull request:** `6890206` (nhánh `chutranphuongnam` đã merge vào `main`)
- **Một quyết định kỹ thuật tôi đã đưa ra và lý do:** Phân định dứt khoát ranh giới giữa `check_service_status` (dịch vụ dùng chung toàn công ty) và `inspect_device` (thiết bị cá nhân) ngay trong tool description để mô hình không bị nhầm lẫn khi người dùng hỏi về sự cố mạng/VPN.
- **Khó khăn tôi gặp và cách tôi xử lý:** Đảm bảo toàn bộ schema JSON và các tên enum trong `tools.yaml` khớp chính xác 100% với signature của các hàm Python trong thư mục `starter_v0/tools/` để evaluator không báo lỗi mismatch.
- **Điều tôi học được từ phần việc này:** Hiểu rõ tool description và schema chính là một phần của prompt định hướng; mô tả càng chặt chẽ thì tỷ lệ chọn sai tool và sai tham số càng giảm rõ rệt.
- **Nếu làm lại, tôi sẽ cải thiện điều gì:** Bổ sung thêm ví dụ minh họa (examples) cho các tham số dạng mảng phức tạp như `findings` trong tool `format_incident_report`.

Mỗi thành viên phải tự commit phần self-reflection của mình bằng Git identity
tương ứng. Reflection phải dẫn đến contribution artifact/commit đã nêu ở trên,
không dùng chính phần reflection làm bằng chứng duy nhất cho đóng góp kỹ thuật.

## C3. Final checkout

Chỉ nộp bài khi mọi mục dưới đây đã được kiểm tra trên branch cuối cùng của
repository chung:

- [ ] `TEAMMATES.md` có đủ họ tên, MSSV, GitHub username và vai trò.
- [ ] Mỗi thành viên có ít nhất một commit trong lịch sử branch nộp bài.
- [ ] Phần reflection chung của nhóm đã hoàn thành và có evidence.
- [ ] Mỗi thành viên đã tự viết và commit self-reflection của mình.
- [ ] `system_prompt.md`, `tools.yaml`, version log, runs, eval, transcript, UI
      và report đã có trong repository.
- [ ] Không có `.env`, API key, token, dữ liệu thật, cache hoặc generated ticket.
- [ ] Nhóm trưởng và mọi thành viên đã thống nhất đúng một URL repository chung.
- [ ] Nhóm trưởng và mọi thành viên sẽ nộp cùng URL đó trên VLearn.

**URL repository chung dùng để nộp:**

> URL:
