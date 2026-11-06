# Phân tích lỗi V1 so với B0

- A: `runs/mt/B0/fleurs_dev_asr_pho/hyp.jsonl`
- B: `runs/mt/V1/fleurs_dev_asr_pho/hyp.jsonl`

| Nhóm | n | BLEU B0 | BLEU V1 | chrF++ B0 | chrF++ V1 |
|---|---|---|---|---|---|
| all | 361 | 22.96 | 26.47 | 50.4 | 52.48 |
| so | 44 | 10.86 | 18.29 | 41.85 | 46.76 |
| ten | 210 | 20.3 | 25.26 | 48.28 | 51.42 |
| dai | 54 | 16.55 | 22.54 | 48.34 | 51.29 |
| asr_xau | 31 | 7.86 | 16.01 | 37.29 | 43.34 |
| con_lai | 120 | 27.26 | 28.1 | 53.0 | 53.89 |

## V1 kém B0 nhiều nhất (chrF++ câu)

**3933225803333432591.wav** (Δ chrF++ -31.7; WER ASR 0.0)
- nguồn (ASR): người tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- B0: The Spanish began a period of colonization that lasted for three centuries.
- V1: The Spanish began a three-century period of colonialism.

**7075452873105516859.wav** (Δ chrF++ -31.7; WER ASR 0.0)
- nguồn (ASR): người tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- B0: The Spanish began a period of colonization that lasted for three centuries.
- V1: The Spanish began a three-century period of colonialism.

**11660335130988953907.wav** (Δ chrF++ -25.5; WER ASR 17.647058823529413)
- nguồn (ASR): lúc đầu trang phục chịu ảnh hưởng nặng nề của nền văn hoá bayern tin ở phía đông.
- tham chiếu: At the beginning dress was heavily influenced by the Byzantine culture in the east.
- B0: At first the dress was heavily influenced by the belief-based Bavarian culture in the east.
- V1: At first the costumes were heavily influenced by the Eastern Bavarian culture.

**11968837672136740842.wav** (Δ chrF++ -25.3; WER ASR 9.090909090909092)
- nguồn (ASR): hầu hết các quận được phục vụ bởi lòi xe buýt costa nhỏ của nhật vốn rất thoải mái và chắc chắn.
- tham chiếu: Most districts are served by small Japanese Coaster Buses, which are comfortable and sturdy.
- B0: Most of the districts are served by small japanese costa buses, which are comfortable and sturdy.
- V1: Most of the districts are served by the comfortable and sturdy “Costa" bus.

**10571565832044041622.wav** (Δ chrF++ -24.2; WER ASR 17.647058823529413)
- nguồn (ASR): lúc đầu trang phục chịu ảnh hưởng nặng nề của nền văn hoá bikini tin ở phía đông.
- tham chiếu: At the beginning dress was heavily influenced by the Byzantine culture in the east.
- B0: At first the dress was heavily influenced by the private bikini culture in the east.
- V1: At first, the costumes were heavily influenced by the Eastern culture of the Bikini.

**8256624191026535095.wav** (Δ chrF++ -21.4; WER ASR 3.3333333333333335)
- nguồn (ASR): tai nạn không lưu rất thường xảy ra ở iraq nơi có đội tàu cũ kỹ được bảo trì kém trong những hoạt động cả quân sự lẫn dân sự.
- tham chiếu: Air accidents are common in Iran, which has an aging fleet that is poorly maintained both for civil and military operations.
- B0: Air traffic accidents are common in iraq, which has an aging fleet that is poorly maintained in both military and civilian operations.
- V1: Air traffic accidents are common in Iraq, where there are old, poorly maintained fleets in both military and civilian operations.

**14207419599805557425.wav** (Δ chrF++ -19.1; WER ASR 0.0)
- nguồn (ASR): tai nạn không lưu rất thường xảy ra ở iran nơi có đội tàu cũ kỹ được bảo trì kém trong những hoạt động cả quân sự lẫn dân sự.
- tham chiếu: Air accidents are common in Iran, which has an aging fleet that is poorly maintained both for civil and military operations.
- B0: Air traffic accidents are common in iran, which has an aging fleet that is poorly maintained in both military and civilian operations.
- V1: Air traffic accidents are common in Iran, where there are old, poorly maintained fleets in both military and civilian operations.

**17828912951962548419.wav** (Δ chrF++ -18.7; WER ASR 5.555555555555555)
- nguồn (ASR): các yếu tố xác định văn hoá vùng miền khác biệt nhau có thể là ngôn ngữ thẩm mỹ công giáo chính trị tình dục địa lý hoặc sự kết hợp của các yếu tố này.
- tham chiếu: The qualities that determine a subculture as distinct may be linguistic, aesthetic, religious, political, sexual, geographical, or a combination of factors.
- B0: The factors that define different regional cultures can be linguistic, aesthetic, religious, political, sexual, geographic, or a combination of these.
- V1: The factors that define distinct regional cultures can be language, aesthetics, Catholicism, politics, sexuality, geography, or a combination of these.


## V1 hơn B0 nhiều nhất (chrF++ câu)

**7985674771975971897.wav** (Δ chrF++ +39.8; WER ASR 7.6923076923076925)
- nguồn (ASR): tổng thống mỹ george bush nhiệt liệt hoan nghênh thông báo này.
- tham chiếu: U.S. President George W. Bush welcomed the announcement.
- B0: U.S. president george bush warmly welcomed this announcement.
- V1: U.S. President George W. Bush warmly welcomed the announcement.

**11024498478308479354.wav** (Δ chrF++ +39.8; WER ASR 15.384615384615385)
- nguồn (ASR): tổng thống mỹ george tuýp lưu bush nhiệt liệt hoan nghênh thông báo này.
- tham chiếu: U.S. President George W. Bush welcomed the announcement.
- B0: U.S. president george bush warmly welcomed this announcement.
- V1: U.S. President George W. Bush warmly welcomed the announcement.

**639768829445504427.wav** (Δ chrF++ +29.1; WER ASR 47.36842105263158)
- nguồn (ASR): trong số một ngàn bốn trăm người tham gia thăm dò ý kiến trước kỳ bầu cử liên bang năm hai ngàn không trăm mười số người phản đối việc úc trở thành một nước cộng hòa tăng thêm tám phần trăm so với năm hai ngàn không trăm linh tám.
- tham chiếu: Out of 1,400 people polled prior to the 2010 federal election, those who oppose Australia becoming a republic grew by 8 per cent since 2008.
- B0: Of the one thousand and four hundred people polled before the federal election, five two thousand and eighteen opposed the establishment of australia as a republic, up eight percent from five two thousand and eighteen.
- V1: Of the 14,100 people polled prior to the 2010 federal election, 8 percent opposed Australia becoming a republic, up from 2008.

**4891217210315836503.wav** (Δ chrF++ +28.9; WER ASR 18.75)
- nguồn (ASR): quần đảo đông phi thuộc ánh lù dương gần bờ biển phía đông của giao phi.
- tham chiếu: The East African Islands are in the Indian Ocean off the eastern coast of Africa.
- B0: The eastern africa archipelago belongs to the glare near the eastern coast of giao phi.
- V1: The East African Islands are in the Pacific Ocean near the east coast of the African Islands.
