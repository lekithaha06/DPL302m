# Danh mục toàn bộ code

142 file code và cấu hình. Bản gom nguyên văn kèm output: `notebooks/00_toan_bo_code.ipynb`.

## Dữ liệu: tải, làm sạch, chống rò rỉ, EDA, cân bằng (7 file)

- `experiments/scripts/data/gan_mien_flores.py`
- `experiments/scripts/data/ham_dung_chung.py`
- `experiments/scripts/data/viec1_tai_3_bo_du_lieu.py`
- `experiments/scripts/data/viec2_ghep_chia_fleurs_chong_trung.py`
- `experiments/scripts/data/viec2_lam_sach_du_lieu.py`
- `experiments/scripts/data/viec3_eda.py`
- `experiments/scripts/data/viec4_can_bang_du_lieu.py`

## Khối nghe: suy luận, chấm điểm, phân tích lỗi (19 file)

- `configs/asr_protocol.json`
- `configs/ban_chot.json`
- `configs/common_suppression_from_task1.json`
- `configs/V3.json`
- `configs/V4.json`
- `experiments/configs/asr_protocol.json`
- `experiments/configs/common_suppression_from_task1.json`
- `experiments/configs/README_CAU_HINH.txt`
- `experiments/scripts/asr/bootstrap_wer.py`
- `experiments/scripts/asr/dien_gia_thuyet.py`
- `experiments/scripts/asr/error_audit.py`
- `experiments/scripts/asr/make_asr_manifest.py`
- `experiments/scripts/asr/README_CHAM_DIEM.txt`
- `experiments/scripts/asr/run_asr.py`
- `experiments/scripts/asr/score_asr.py`
- `experiments/scripts/asr/tao_ds_nghe_kiem.py`
- `experiments/scripts/asr/test_score_asr.py`
- `experiments/scripts/asr/tone_confusion.py`
- `experiments/scripts/asr/tong_hop_asr.py`

## Baseline end-to-end B1 Whisper Translate (7 file)

- `experiments/scripts/baseline2/b1_whisper_translate.py`
- `experiments/scripts/baseline2/ban_giao_goc/b1_whisper_translate/evaluate_b1.py`
- `experiments/scripts/baseline2/ban_giao_goc/b1_whisper_translate/inference.py`
- `experiments/scripts/baseline2/ban_giao_goc/b1_whisper_translate/requirements.txt`
- `experiments/scripts/baseline2/ban_giao_goc/b1_whisper_translate/run_fleurs_test.py`
- `experiments/scripts/baseline2/ban_giao_goc/check_data.py`
- `experiments/scripts/baseline2/ban_giao_goc/verify_b0.py`

## Khối dịch: dữ liệu, huấn luyện LoRA V1–V4, dịch, bootstrap (15 file)

- `experiments/configs/mt/A_aug.json`
- `experiments/configs/mt/A_r32.json`
- `experiments/configs/mt/A_r8.json`
- `experiments/configs/mt/V1.json`
- `experiments/configs/mt/V2.json`
- `experiments/configs/mt/V3.json`
- `experiments/configs/mt/V4.json`
- `experiments/scripts/mt/bootstrap.py`
- `experiments/scripts/mt/do_toc_do.py`
- `experiments/scripts/mt/failure_analysis.py`
- `experiments/scripts/mt/make_aug_data.py`
- `experiments/scripts/mt/make_balanced_data.py`
- `experiments/scripts/mt/make_mt_data.py`
- `experiments/scripts/mt/train_lora.py`
- `experiments/scripts/mt/translate.py`

## Chọn bản cuối, ablation, đánh giá tổng hợp (4 file)

- `experiments/scripts/cham_theo_mien.py`
- `experiments/scripts/he_thong_bootstrap.py`
- `experiments/scripts/ket_luan.py`
- `experiments/scripts/ve_bieu_do.py`

## Kiểm tra 3 seed (3 file)

- `experiments/scripts/modal_3seed.py`
- `experiments/scripts/tao_notebook_3seed.py`
- `experiments/scripts/tong_hop_3seed.py`

## Độ bền khối nghe (3 file)

- `experiments/scripts/asr/tao_audio_robust.py`
- `experiments/scripts/hang_doi_robust.sh`
- `experiments/scripts/tao_notebook_robust.py`

## Sản phẩm: pipeline, API, demo, Docker, CI (25 file)

- `.dockerignore`
- `.env.example`
- `.github/workflows/ci.yml`
- `.gitignore`
- `api/__init__.py`
- `api/main.py`
- `app/gradio_app.py`
- `docker/docker-compose.yml`
- `docker/Dockerfile.api`
- `docker/Dockerfile.app`
- `docker/requirements-app.txt`
- `pyproject.toml`
- `pytest.ini`
- `requirements-dev.txt`
- `requirements.txt`
- `src/__init__.py`
- `src/audio.py`
- `src/dataset/__init__.py`
- `src/evaluate.py`
- `src/inference.py`
- `src/models/__init__.py`
- `src/pipeline.py`
- `src/so.py`
- `src/train.py`
- `src/truc_tiep.py`

## Kiểm thử (10 file)

- `tests/__init__.py`
- `tests/danh_gia_proposed.py`
- `tests/nghiem_thu_that.py`
- `tests/test_adapter.py`
- `tests/test_api.py`
- `tests/test_audio.py`
- `tests/test_evaluate.py`
- `tests/test_pipeline.py`
- `tests/test_so.py`
- `tests/test_truc_tiep.py`

## Điều phối, môi trường, sinh notebook và tài liệu (49 file)

- `experiments/chay_lai.sh`
- `experiments/chay_lai_notebook/so_sanh_voi_ban_goc.py`
- `experiments/env/check_env.py`
- `experiments/env/env.sh`
- `experiments/env/pip_freeze.txt`
- `experiments/env/requirements.txt`
- `experiments/nghe_kiem/HUONG_DAN.txt`
- `experiments/scripts/asr/chay_baseline_asr.sh`
- `experiments/scripts/chay_nb07.py`
- `experiments/scripts/chay_notebook.py`
- `experiments/scripts/dong_goi_repo_cuoi.py`
- `experiments/scripts/hang_doi/do_toc_do_lap.sh`
- `experiments/scripts/hang_doi/hang_doi_bo_sung.sh`
- `experiments/scripts/hang_doi/hang_doi_dem1.sh`
- `experiments/scripts/hang_doi/hang_doi_dem2.sh`
- `experiments/scripts/hang_doi/hang_doi_dem2b.sh`
- `experiments/scripts/hang_doi/hang_doi_dem2c.sh`
- `experiments/scripts/hang_doi/hang_doi_ket_thuc.sh`
- `experiments/scripts/hang_doi/hang_doi_phomt.sh`
- `experiments/scripts/hang_doi/hang_doi_v1.sh`
- `experiments/scripts/hang_doi/hang_doi_v2.sh`
- `experiments/scripts/hang_doi/s4_asr_baseline.sh`
- `experiments/scripts/hang_doi_do_V2.sh`
- `experiments/scripts/hang_doi_do_V4.sh`
- `experiments/scripts/hang_doi_he_thong_V2.sh`
- `experiments/scripts/tai_lieu/dien_tai_lieu_bao.py`
- `experiments/scripts/tai_lieu/dong_goi_gui_bao_uyen.py`
- `experiments/scripts/tai_lieu/dong_zip_nop.py`
- `experiments/scripts/tai_lieu/nhom/bao_cao.py`
- `experiments/scripts/tai_lieu/nhom/chung.py`
- `experiments/scripts/tai_lieu/nhom/paper_checklist.py`
- `experiments/scripts/tai_lieu/nhom/script_kiet_de_hoc.py`
- `experiments/scripts/tai_lieu/nhom/slide.py`
- `experiments/scripts/tai_lieu/nhom/slide_khung.py`
- `experiments/scripts/tai_lieu/nhom/tai_lieu_ky_thuat.py`
- `experiments/scripts/tai_lieu/nhom/ve_hinh.py`
- `experiments/scripts/tai_lieu/o_thiet_lap_nb.py`
- `experiments/scripts/tai_lieu/ra_soat_cuoi.py`
- `experiments/scripts/tai_lieu/tao_ban_giao.py`
- `experiments/scripts/tai_lieu/tao_bao_cao.py`
- `experiments/scripts/tai_lieu/tao_checklist.py`
- `experiments/scripts/tai_lieu/tao_notebook_toan_bo.py`
- `experiments/scripts/tai_lieu/tao_slide.py`
- `experiments/scripts/tai_lieu/ve_kien_truc_du_an.py`
- `experiments/scripts/tai_model.py`
- `experiments/scripts/tao_notebook_chay_lai.py`
- `experiments/scripts/tao_notebook_eda_loi.py`
- `experiments/scripts/tao_notebook_gd2.py`
- `experiments/scripts/theo_doi_tai_nguyen.py`
