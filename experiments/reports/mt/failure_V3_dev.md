# Phân tích lỗi V3 so với B0

- A: `runs/mt/B0/fleurs_dev_asr_pho/hyp.jsonl`
- B: `runs/mt/V3/fleurs_dev_asr_pho/hyp.jsonl`

| Nhóm | n | BLEU B0 | BLEU V3 | chrF++ B0 | chrF++ V3 |
|---|---|---|---|---|---|
| all | 361 | 22.96 | 26.71 | 50.4 | 52.5 |
| so | 44 | 10.86 | 18.95 | 41.85 | 46.84 |
| ten | 210 | 20.3 | 24.82 | 48.28 | 51.09 |
| dai | 54 | 16.55 | 21.68 | 48.34 | 50.93 |
| asr_xau | 31 | 7.86 | 16.67 | 37.29 | 43.92 |
| con_lai | 120 | 27.26 | 29.37 | 53.0 | 54.21 |

## V3 kém B0 nhiều nhất (chrF++ câu)

**3933225803333432591.wav** (Δ chrF++ -26.0; WER ASR 0.0)
- nguồn (ASR): người tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- B0: The Spanish began a period of colonization that lasted for three centuries.
- V3: The Spanish started a three-century period of colonialism.

**7075452873105516859.wav** (Δ chrF++ -26.0; WER ASR 0.0)
- nguồn (ASR): người tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- B0: The Spanish began a period of colonization that lasted for three centuries.
- V3: The Spanish started a three-century period of colonialism.

**11356869827794671517.wav** (Δ chrF++ -24.9; WER ASR 7.6923076923076925)
- nguồn (ASR): ngay sau đó cảnh sát được trang bị công cụ chống bạo động tiến vào sân và dồn tù nhân vào gốc bằng hơi cay.
- tham chiếu: Soon, officers equipped with riot gear entered the yard and cornered the inmates with tear gas.
- B0: Soon afterwards police equipped with riot gear entered the yard and cornered the prisoners at the base with tear gas.
- V3: Shortly thereafter, riot-equipped police entered the yard and gassed the prisoners at the base with tear gas.

**11968837672136740842.wav** (Δ chrF++ -19.4; WER ASR 9.090909090909092)
- nguồn (ASR): hầu hết các quận được phục vụ bởi lòi xe buýt costa nhỏ của nhật vốn rất thoải mái và chắc chắn.
- tham chiếu: Most districts are served by small Japanese Coaster Buses, which are comfortable and sturdy.
- B0: Most of the districts are served by small japanese costa buses, which are comfortable and sturdy.
- V3: Most districts are served by the comfortable and sturdy Japan's Little Costa bus.

**17828912951962548419.wav** (Δ chrF++ -18.7; WER ASR 5.555555555555555)
- nguồn (ASR): các yếu tố xác định văn hoá vùng miền khác biệt nhau có thể là ngôn ngữ thẩm mỹ công giáo chính trị tình dục địa lý hoặc sự kết hợp của các yếu tố này.
- tham chiếu: The qualities that determine a subculture as distinct may be linguistic, aesthetic, religious, political, sexual, geographical, or a combination of factors.
- B0: The factors that define different regional cultures can be linguistic, aesthetic, religious, political, sexual, geographic, or a combination of these.
- V3: The factors that define distinct regional cultures can be language, aesthetics, Catholicism, politics, sexuality, geography, or a combination of these.

**12090846728876801190.wav** (Δ chrF++ -16.8; WER ASR 0.0)
- nguồn (ASR): các nhà khoa học cho biết vụ va chạm đã gây ra vụ nổ rất lớn.
- tham chiếu: Scientists say the explosion caused by the collision was massive.
- B0: Scientists say the impact caused a massive explosion.
- V3: The scientists said the impact had caused a very large explosion.

**11025013104549101811.wav** (Δ chrF++ -16.4; WER ASR 10.526315789473685)
- nguồn (ASR): thêm ba quả bom lửa phát đổ gần các tòa nhà chính phủ trong khoảng hai tiếng đồng hồ.
- tham chiếu: Three more bombs exploded near government buildings in a period of two hours.
- B0: Three more incendiary bombs exploded near government buildings in the space of two hours.
- V3: Three more incendiary bombs went off near government buildings in about two hours.

**4767212356465567922.wav** (Δ chrF++ -15.9; WER ASR 21.73913043478261)
- nguồn (ASR): các ca sĩ nổi tiếng trên khắp cả nước trình bày hazard hoặc các bài hát mộ đạo tại trưng cổ sergio higuain.
- tham chiếu: Famous singers across the country presented bhajans, or devotional songs, to Shri Shyam's feet.
- B0: Famous singers across the country present hazard or devotional songs at sergio higuain's gallery.
- V3: Famous singers from all over the country performed "Hanger" or devotional songs at the UNESCO World Heritage site, Sergio Higuain.


## V3 hơn B0 nhiều nhất (chrF++ câu)

**4891217210315836503.wav** (Δ chrF++ +34.0; WER ASR 18.75)
- nguồn (ASR): quần đảo đông phi thuộc ánh lù dương gần bờ biển phía đông của giao phi.
- tham chiếu: The East African Islands are in the Indian Ocean off the eastern coast of Africa.
- B0: The eastern africa archipelago belongs to the glare near the eastern coast of giao phi.
- V3: The East African Islands are in the Southern Ocean near the eastern coast of Cape Verde.

**11024498478308479354.wav** (Δ chrF++ +30.6; WER ASR 15.384615384615385)
- nguồn (ASR): tổng thống mỹ george tuýp lưu bush nhiệt liệt hoan nghênh thông báo này.
- tham chiếu: U.S. President George W. Bush welcomed the announcement.
- B0: U.S. president george bush warmly welcomed this announcement.
- V3: U.S. President George T. Bush warmly welcomed the announcement.

**639768829445504427.wav** (Δ chrF++ +30.4; WER ASR 47.36842105263158)
- nguồn (ASR): trong số một ngàn bốn trăm người tham gia thăm dò ý kiến trước kỳ bầu cử liên bang năm hai ngàn không trăm mười số người phản đối việc úc trở thành một nước cộng hòa tăng thêm tám phần trăm so với năm hai ngàn không trăm linh tám.
- tham chiếu: Out of 1,400 people polled prior to the 2010 federal election, those who oppose Australia becoming a republic grew by 8 per cent since 2008.
- B0: Of the one thousand and four hundred people polled before the federal election, five two thousand and eighteen opposed the establishment of australia as a republic, up eight percent from five two thousand and eighteen.
- V3: Of the 1,400 people polled prior to the 2010 federal election, 8 percent opposed Australia becoming a republic, up from 2008, 8 percent.

**8475030330177401998.wav** (Δ chrF++ +28.6; WER ASR 0.0)
- nguồn (ASR): điều đó dường như không hợp lý đối với tôi điều đó chắc chắn không công bằng.
- tham chiếu: That didn't seem to make sense to me; it certainly wasn't fair.
- B0: That doesn't seem fair to me, that's certainly not fair.
- V3: That doesn't seem to make sense to me. It certainly isn't fair.
