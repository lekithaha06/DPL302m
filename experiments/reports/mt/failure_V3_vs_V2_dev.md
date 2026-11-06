# Phân tích lỗi V3 so với V2

- A: `runs/mt/V2/fleurs_dev_asr_pho/hyp.jsonl`
- B: `runs/mt/V3/fleurs_dev_asr_pho/hyp.jsonl`

| Nhóm | n | BLEU V2 | BLEU V3 | chrF++ V2 | chrF++ V3 |
|---|---|---|---|---|---|
| all | 361 | 26.45 | 26.71 | 52.74 | 52.5 |
| so | 44 | 18.78 | 18.95 | 48.43 | 46.84 |
| ten | 210 | 25.28 | 24.82 | 51.99 | 51.09 |
| dai | 54 | 22.44 | 21.68 | 52.34 | 50.93 |
| asr_xau | 31 | 15.69 | 16.67 | 44.82 | 43.92 |
| con_lai | 120 | 27.26 | 29.37 | 52.94 | 54.21 |

## V3 kém V2 nhiều nhất (chrF++ câu)

**3933225803333432591.wav** (Δ chrF++ -26.0; WER ASR 0.0)
- nguồn (ASR): người tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- V2: The Spanish began a period of colonization that lasted for three centuries.
- V3: The Spanish started a three-century period of colonialism.

**7075452873105516859.wav** (Δ chrF++ -26.0; WER ASR 0.0)
- nguồn (ASR): người tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- V2: The Spanish began a period of colonization that lasted for three centuries.
- V3: The Spanish started a three-century period of colonialism.

**9355854015001115119.wav** (Δ chrF++ -24.2; WER ASR 5.882352941176471)
- nguồn (ASR): nghị tây ban nha đã mở đầu thời kỳ thực dân kéo dài suốt ba thế kỷ.
- tham chiếu: The Spaniards started the colonization period which lasted for three centuries.
- V2: The Spanish conquest began a period of colonialism that lasted for three centuries.
- V3: The Spanish conquest began a three-century period of colonialism.

**4397767911643995825.wav** (Δ chrF++ -17.6; WER ASR 29.62962962962963)
- nguồn (ASR): người bồ đào nha đã phá hủy và xây dựng lại nó dưới cái tên kaserang ca và chỉ bỏ hoang sau trận động đất năm một nghìn bảy trăm năm lăm.
- tham chiếu: The Portuguese destroyed it and rebuilt it under the name Casa Branca, only to abandon it after an earthquake in 1755.
- V2: The Portuguese destroyed it and rebuilt it under the name "Kascaraca" and only abandoned it after the 1755 earthquake.
- V3: It was destroyed and rebuilt by the Portuguese under the name Kaserangca and abandoned only after the 1775 earthquake.

**12090846728876801190.wav** (Δ chrF++ -16.8; WER ASR 0.0)
- nguồn (ASR): các nhà khoa học cho biết vụ va chạm đã gây ra vụ nổ rất lớn.
- tham chiếu: Scientists say the explosion caused by the collision was massive.
- V2: Scientists say the impact caused a massive explosion.
- V3: The scientists said the impact had caused a very large explosion.

**13121441893039387178.wav** (Δ chrF++ -16.2; WER ASR 0.0)
- nguồn (ASR): côn trùng là những động vật đầu tiên bay vào không trung khả năng bay giúp chúng tránh kẻ thù dễ dàng hơn và tìm kiếm thức ăn và bạn tình hiệu quả hơn.
- tham chiếu: Insects were the first animals to take to the air. Their ability to fly helped them evade enemies more easily and find food and mates more efficiently.
- V2: Insects were the first animals to enter the air. Their ability to fly made it easier for them to avoid predators and to find food and mates more efficiently.
- V3: Insects were the first animals to enter the air. Their flight ability made it easier for them to avoid predators and more effective in finding food and mates.

**15536072470715945819.wav** (Δ chrF++ -15.5; WER ASR 27.77777777777778)
- nguồn (ASR): ở arsenal có một trong những đội bóng bô loa và cầu thủ giỏi nhất thế giới.
- tham chiếu: Argentina is well known for having one of the best polo teams and players in the world.
- V2: Arsenal has one of the best football teams and players in the world.
- V3: Arsenal has one of the world's best football teams and players.

**2180101209324633057.wav** (Δ chrF++ -14.8; WER ASR 33.333333333333336)
- nguồn (ASR): con tem thứ một ngàn của anh ấy là bức tranh tráng lợi chứng thư vĩ đại của các vị vua thời điểm của david luật kơ erdogan sachs năm hai ngàn được việt kê trong sách kỷ lục united thế giới.
- tham chiếu: His 1,000th stamp was the magnificent "Great Deeds by Swedish Kings" by David Klöcker Ehrenstrahl in 2000, which is listed in the Guinness Book of World Records.
- V2: His 1,000th stamp is a painting of the "Great Deeds of Kings" by David Lawyer, published in 2000, listed in the United World Records.
- V3: His 1st stamp was the famous painting "The Great Deed of Kings", dated to 2, 000 AD, listed in the United World Records.


## V3 hơn V2 nhiều nhất (chrF++ câu)

**795551268484288954.wav** (Δ chrF++ +32.3; WER ASR 10.0)
- nguồn (ASR): ngay sau khi bạn thoát khỏi dòng nước suối việc bê trở lại không còn khó khăn hơn bình thường.
- tham chiếu: As soon as you get out of the current, swimming back is no more difficult than normally.
- V2: As soon as you're out of the stream, it's no harder to come back.
- V3: As soon as you get out of the stream, getting back in is no more difficult than it used to be.

**6599292211497398479.wav** (Δ chrF++ +32.3; WER ASR 10.0)
- nguồn (ASR): ngay sau khi bạn thoát khỏi dòng nước suối việc bê trở lại không còn khó khăn hơn bình thường.
- tham chiếu: As soon as you get out of the current, swimming back is no more difficult than normally.
- V2: As soon as you're out of the stream, it's no harder to come back.
- V3: As soon as you get out of the stream, getting back in is no more difficult than it used to be.

**12452598771625453983.wav** (Δ chrF++ +24.1; WER ASR 0.0)
- nguồn (ASR): dân số ban đầu hoàn toàn không thay đổi họ vẫn cần sự thích nghi như trước kia.
- tham chiếu: The original population hasn't changed at all, they still need the same adaptations as before.
- V2: The original population was completely unchanged; they still needed the same adaptations.
- V3: The original population has not changed at all. They still need the same adaptations as before.

**9573923728449838180.wav** (Δ chrF++ +22.6; WER ASR 0.0)
- nguồn (ASR): vệ tinh trong không gian nhận cuộc gọi và sau đó phản lại xuống gần như tức thì.
- tham chiếu: The satellite in space gets the call and then reflects it back down, almost instantly.
- V2: Satellites in space receive a call and then respond to it almost instantly.
- V3: The satellite in space receives the call and then sends it back down almost instantly.
