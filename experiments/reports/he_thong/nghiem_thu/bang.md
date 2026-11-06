# Nghiem thu model that

Ngay 03/11/2026 16:13 · {'python': '3.11.1', 'may': 'Windows-10-10.0.26200-SP0', 'torch': '2.0.1+cu117', 'cuda': True, 'gpu': 'NVIDIA GeForce RTX 4060 Laptop GPU', 'transformers': '4.44.2', 'gradio': '4.44.1'}

| Ma | Bai kiem tra | Ket qua |
|---|---|---|
| T07 | Nap loi | DAT |
| T01/F01 | Audio that | DAT |
| T03/F03 | Audio dai | DAT |
| T04/F05 | Im lang / giong nho | DAT |
| T05/F08 | Dinh dang | **TRUOT** |
| T09/F10 | 10 luot | DAT |
| T08/F06 | Doi phien ban | DAT |

Chua tu dong: T02 (micro 45-60 s tren trinh duyet) va T09 phan 2 tab GUI, T10 (pytest + ruff + docker). Kiem bang tay theo README muc Nghiem thu.

## Chi tiet

### T07 Nap loi

```
FileNotFoundError: khong thay adapter khong_ton_tai\V9
```

### T01/F01 Audio that

```
vinai/PhoWhisper-small@a86b604c + vinai/vinai-translate-vi2en-v2@ae7baa85 + LoRA V4/best
    dev1_16525570830762756295.wav: VI='các ví dụ về hoạt động tại chỗ lao gầm săn bắn câu cá chụp ảnh ngắm chim và tham' | EN='Examples of on-site activities: roaring, hunting, fishing, photography, bird wat' | RTF 0.387
    dev2_13754775770768255557.wav: VI='nghiên cứu trí tuệ nhân tạo bao gồm tạo ra những cỗ máy tự động hóa các tác dụ đ' | EN='The study of artificial intelligence involves creating machines that automate ar' | RTF 0.107
    dev3_15730294784062856962.wav: VI='chi phí chiến tranh của chủ nghĩa đế quốc hoa kỳ trong cuộc trình phạt philippin' | EN='The cost of American imperialism in the Philippines was paid by the Filipinos th' | RTF 0.130
    -> NGUOI KIEM phai doc lai: noi dung VI/EN co dung voi audio khong
```

### T03/F03 Audio dai

```
1 phut: 3 doan, dai nhat 20.8 s, lien nhau=True, phu het=True, doan rong=0, xu ly 7.0 s
    3 phut: 7 doan, dai nhat 26.0 s, lien nhau=True, phu het=True, doan rong=0, xu ly 21.2 s
    5 phut: 12 doan, dai nhat 27.8 s, lien nhau=True, phu het=True, doan rong=0, xu ly 32.5 s
    -> NGUOI KIEM nghe cho noi 2 doan: co lap/mat chu khong
```

### T04/F05 Im lang / giong nho

```
im lang 3 s -> 0 doan, ''; giong nho -50 dBFS -> 'các ví dụ về hoạt động tại chỗ lao gầm săn bắn câu cá chụp ảnh ngắm chim và tham'
```

### T05/F08 Dinh dang

```
khong co ffmpeg trong PATH: m4a/webm se khong doc duoc
```

### T09/F10 10 luot

```
3 file x 10 luot, ket qua lap lai giong lan dau = True
```

### T08/F06 Doi phien ban

```
V4 mac dinh: vinai/PhoWhisper-small@a86b604c + vinai/vinai-translate-vi2en-v2@ae7baa85 + LoRA V4/best
      EN='Examples of on-site activities: roaring, hunting, fishing, photography, bird watching and '
    V3: vinai/PhoWhisper-small@a86b604c + vinai/vinai-translate-vi2en-v2@ae7baa85 + LoRA V3/best
      EN='Examples of on-site activities include roaring, hunting, fishing, photography, bird watchi'
    B0: vinai/PhoWhisper-small@a86b604c + vinai/vinai-translate-vi2en-v2@ae7baa85 + LoRA khong (B0)
      EN='examples of on-site activities roaring hunting fishing birdwatching photography and park t'
    ban dich 3 ban giong nhau het: False (giong het thi nghi adapter khong duoc nap)
```
