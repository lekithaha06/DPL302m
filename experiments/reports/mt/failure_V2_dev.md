# Phân tích lỗi V2 so với B0

- A: `runs/mt/B0/fleurs_dev_asr_pho/hyp.jsonl`
- B: `runs/mt/V2/fleurs_dev_asr_pho/hyp.jsonl`

| Nhóm | n | BLEU B0 | BLEU V2 | chrF++ B0 | chrF++ V2 |
|---|---|---|---|---|---|
| all | 361 | 22.96 | 26.45 | 50.4 | 52.74 |
| so | 44 | 10.86 | 18.78 | 41.85 | 48.43 |
| ten | 210 | 20.3 | 25.28 | 48.28 | 51.99 |
| dai | 54 | 16.55 | 22.44 | 48.34 | 52.34 |
| asr_xau | 31 | 7.86 | 15.69 | 37.29 | 44.82 |
| con_lai | 120 | 27.26 | 27.26 | 53.0 | 52.94 |

## V2 kém B0 nhiều nhất (chrF++ câu)

**11356869827794671517.wav** (Δ chrF++ -33.8; WER ASR 7.6923076923076925)
- nguồn (ASR): ngay sau đó cảnh sát được trang bị công cụ chống bạo động tiến vào sân và dồn tù nhân vào gốc bằng hơi cay.
- tham chiếu: Soon, officers equipped with riot gear entered the yard and cornered the inmates with tear gas.
- B0: Soon afterwards police equipped with riot gear entered the yard and cornered the prisoners at the base with tear gas.
- V2: Soon afterwards, riot-equipped police entered the yard and gassed the prisoners at the base.

**10571565832044041622.wav** (Δ chrF++ -25.0; WER ASR 17.647058823529413)
- nguồn (ASR): lúc đầu trang phục chịu ảnh hưởng nặng nề của nền văn hoá bikini tin ở phía đông.
- tham chiếu: At the beginning dress was heavily influenced by the Byzantine culture in the east.
- B0: At first the dress was heavily influenced by the private bikini culture in the east.
- V2: At first, the costumes were heavily influenced by the cultures of the Far East.

**8256624191026535095.wav** (Δ chrF++ -24.6; WER ASR 3.3333333333333335)
- nguồn (ASR): tai nạn không lưu rất thường xảy ra ở iraq nơi có đội tàu cũ kỹ được bảo trì kém trong những hoạt động cả quân sự lẫn dân sự.
- tham chiếu: Air accidents are common in Iran, which has an aging fleet that is poorly maintained both for civil and military operations.
- B0: Air traffic accidents are common in iraq, which has an aging fleet that is poorly maintained in both military and civilian operations.
- V2: Air traffic accidents are very common in Iraq, where there are old, poorly maintained fleets of both military and civilian operations.

**11660335130988953907.wav** (Δ chrF++ -24.5; WER ASR 17.647058823529413)
- nguồn (ASR): lúc đầu trang phục chịu ảnh hưởng nặng nề của nền văn hoá bayern tin ở phía đông.
- tham chiếu: At the beginning dress was heavily influenced by the Byzantine culture in the east.
- B0: At first the dress was heavily influenced by the belief-based Bavarian culture in the east.
- V2: At first, the costumes were heavily influenced by the culture of the Far East.

**11968837672136740842.wav** (Δ chrF++ -24.2; WER ASR 9.090909090909092)
- nguồn (ASR): hầu hết các quận được phục vụ bởi lòi xe buýt costa nhỏ của nhật vốn rất thoải mái và chắc chắn.
- tham chiếu: Most districts are served by small Japanese Coaster Buses, which are comfortable and sturdy.
- B0: Most of the districts are served by small japanese costa buses, which are comfortable and sturdy.
- V2: Most of the districts are served by Japan's small bus station, which is very comfortable and reliable.

**6599292211497398479.wav** (Δ chrF++ -23.6; WER ASR 10.0)
- nguồn (ASR): ngay sau khi bạn thoát khỏi dòng nước suối việc bê trở lại không còn khó khăn hơn bình thường.
- tham chiếu: As soon as you get out of the current, swimming back is no more difficult than normally.
- B0: as soon as you get out of the stream water the calves come back no more difficult than usual.
- V2: As soon as you're out of the stream, it's no harder to come back.

**795551268484288954.wav** (Δ chrF++ -23.6; WER ASR 10.0)
- nguồn (ASR): ngay sau khi bạn thoát khỏi dòng nước suối việc bê trở lại không còn khó khăn hơn bình thường.
- tham chiếu: As soon as you get out of the current, swimming back is no more difficult than normally.
- B0: as soon as you get out of the stream water the calves come back no more difficult than usual.
- V2: As soon as you're out of the stream, it's no harder to come back.

**9246964791575316688.wav** (Δ chrF++ -23.0; WER ASR 5.555555555555555)
- nguồn (ASR): dân số ban đầu hoàn toàn không thay đổi họ vẫn toàn sự thích nghi như trước kia.
- tham chiếu: The original population hasn't changed at all, they still need the same adaptations as before.
- B0: The original population hasn't changed at all, they're just as adaptive as they were before.
- V2: The original population was completely unchanged; they were just as well adapted as they were before.


## V2 hơn B0 nhiều nhất (chrF++ câu)

**7985674771975971897.wav** (Δ chrF++ +39.8; WER ASR 7.6923076923076925)
- nguồn (ASR): tổng thống mỹ george bush nhiệt liệt hoan nghênh thông báo này.
- tham chiếu: U.S. President George W. Bush welcomed the announcement.
- B0: U.S. president george bush warmly welcomed this announcement.
- V2: U.S. President George W. Bush warmly welcomed the announcement.

**11024498478308479354.wav** (Δ chrF++ +39.8; WER ASR 15.384615384615385)
- nguồn (ASR): tổng thống mỹ george tuýp lưu bush nhiệt liệt hoan nghênh thông báo này.
- tham chiếu: U.S. President George W. Bush welcomed the announcement.
- B0: U.S. president george bush warmly welcomed this announcement.
- V2: U.S. President George W. Bush warmly welcomed the announcement.

**1129769741125387813.wav** (Δ chrF++ +24.8; WER ASR 25.641025641025642)
- nguồn (ASR): conte thứ một ngàn của anh ấy là bức tranh tráng lệ chứng thư vĩ đại của các vị vua thụy điển của david locker allen jones năm hai ngàn được liệt kê trong sách kỷ lục premier thế giới.
- tham chiếu: His 1,000th stamp was the magnificent "Great Deeds by Swedish Kings" by David Klöcker Ehrenstrahl in 2000, which is listed in the Guinness Book of World Records.
- B0: His conte a thousand is david locker allen jones' magnificent painting of the great deed of the kings of swedish five two thousand listed in the book of world premier records.
- V2: His 1000th is a magnificent painting, The Great Deed of the Kings of Sweden by David Locker, Allen Jones in 2000 is listed in the Guinness Book of World Records.

**639768829445504427.wav** (Δ chrF++ +24.1; WER ASR 47.36842105263158)
- nguồn (ASR): trong số một ngàn bốn trăm người tham gia thăm dò ý kiến trước kỳ bầu cử liên bang năm hai ngàn không trăm mười số người phản đối việc úc trở thành một nước cộng hòa tăng thêm tám phần trăm so với năm hai ngàn không trăm linh tám.
- tham chiếu: Out of 1,400 people polled prior to the 2010 federal election, those who oppose Australia becoming a republic grew by 8 per cent since 2008.
- B0: Of the one thousand and four hundred people polled before the federal election, five two thousand and eighteen opposed the establishment of australia as a republic, up eight percent from five two thousand and eighteen.
- V2: Of the 400 voters polled prior to the 2010 federal election, 10 percent opposed Australia becoming a republic, up 8 percent from 2008.
