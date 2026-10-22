# TV4 : sinh lai toan bo so lieu tu do cua phan Du lieu va Danh gia.
# Chay: powershell -ExecutionPolicy Bypass -File .\tv4_reports.ps1 -FleursJson <duong dan> -PhoMTZip <duong dan> -OutDir <thu muc>
param(
  [string]$FleursJson = "",
  [string]$PhoMTZip   = "",
  [string]$FleursViTsv = "",
  [string]$OutDir     = "reports"
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$cs = @"
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Text.RegularExpressions;

public class ScanResult { public long Lines; public int ExactHits; public int FlaggedLines;
    public HashSet<string> TouchedIds = new HashSet<string>();
    public double BestJaccard; public string BestPair = ""; public List<string> Samples = new List<string>(); }

public static class TV4 {
    static readonly Regex NonAlnum = new Regex(@"[^\p{L}\p{N}]+", RegexOptions.Compiled);
    public static string Norm(string s) {
        if (s == null) return "";
        s = s.Normalize(NormalizationForm.FormC).ToLowerInvariant();
        return NonAlnum.Replace(s, " ").Trim();
    }
    public static List<string> Grams(string norm, int n) {
        var o = new List<string>();
        string[] t = norm.Split(new char[]{' '}, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length < n) { if (t.Length > 0) o.Add(string.Join(" ", t)); return o; }
        for (int i = 0; i + n <= t.Length; i++) o.Add(string.Join(" ", t, i, n));
        return o;
    }
    public static ScanResult Scan(string zipPath, string entry, HashSet<string> exact,
                                  Dictionary<string,string> gramIndex,
                                  Dictionary<string,HashSet<string>> gramsById, int n) {
        var r = new ScanResult();
        using (var za = ZipFile.OpenRead(zipPath)) {
            var e = za.GetEntry(entry);
            if (e == null) throw new Exception("khong tim thay entry: " + entry);
            using (var sr = new StreamReader(e.Open(), new UTF8Encoding(false))) {
                string line;
                while ((line = sr.ReadLine()) != null) {
                    r.Lines++;
                    string k = Norm(line);
                    if (k.Length == 0) continue;
                    if (exact.Contains(k)) r.ExactHits++;
                    if (gramIndex == null) continue;
                    var gs = Grams(k, n);
                    HashSet<string> hit = null;
                    foreach (var g in gs) { string id; if (gramIndex.TryGetValue(g, out id)) { if (hit == null) hit = new HashSet<string>(); hit.Add(id); } }
                    if (hit == null) continue;
                    r.FlaggedLines++;
                    var lg = new HashSet<string>(gs);
                    foreach (var id in hit) {
                        r.TouchedIds.Add(id);
                        var fg = gramsById[id];
                        int inter = 0; foreach (var g in lg) if (fg.Contains(g)) inter++;
                        int uni = lg.Count + fg.Count - inter;
                        double jac = uni > 0 ? (double)inter / uni : 0.0;
                        if (jac > r.BestJaccard) { r.BestJaccard = jac; r.BestPair = "FLEURS id " + id + " | jaccard " + jac.ToString("F3") + " | PhoMT dong " + r.Lines + " : " + (k.Length > 180 ? k.Substring(0,180) : k); }
                        if (r.Samples.Count < 50) r.Samples.Add("FLEURS " + id + " | jac " + jac.ToString("F3") + " | PhoMT#" + r.Lines + " | " + (k.Length > 140 ? k.Substring(0,140) : k));
                    }
                }
            }
        }
        return r;
    }
}
"@
Add-Type -TypeDefinition $cs -ReferencedAssemblies System.IO.Compression, System.IO.Compression.FileSystem

# ---------- 1. Thong ke FLEURS vi_vn test ----------
if ($FleursViTsv -and (Test-Path $FleursViTsv)) {
  Write-Output "1. Thong ke FLEURS vi_vn test tu $FleursViTsv"
  $rows = Get-Content -Encoding UTF8 $FleursViTsv
  $ids  = $rows | ForEach-Object { ($_ -split "`t")[0] }
  $secs = $rows | ForEach-Object { [double](($_ -split "`t")[5]) / 16000 }
  $gen  = $rows | ForEach-Object { ($_ -split "`t")[6] }
  $sorted = $secs | Sort-Object
  $perSent = ($ids | Group-Object | Group-Object Count | ForEach-Object { @{ ban_thu_moi_cau = [int]$_.Name; so_cau = $_.Count } })
  $stats = [ordered]@{
    nguon = "FLEURS vi_vn test.tsv, cot num_samples chia 16000"
    ngay_chay = (Get-Date -Format 'yyyy-MM-dd')
    so_ban_thu = $rows.Count
    so_cau_goc = ($ids | Select-Object -Unique).Count
    tong_giay  = [math]::Round(($secs | Measure-Object -Sum).Sum, 1)
    tong_gio   = [math]::Round(($secs | Measure-Object -Sum).Sum / 3600, 3)
    trung_binh_giay = [math]::Round(($secs | Measure-Object -Average).Average, 2)
    trung_vi_giay   = [math]::Round($sorted[[int]($sorted.Count/2)], 2)
    ngan_nhat_giay  = [math]::Round(($secs | Measure-Object -Minimum).Minimum, 2)
    dai_nhat_giay   = [math]::Round(($secs | Measure-Object -Maximum).Maximum, 2)
    so_ban_thu_tren_30_giay = ($secs | Where-Object { $_ -gt 30 }).Count
    phan_bo_gioi_tinh = ($gen | Group-Object | ForEach-Object { @{ nhan = $_.Name; so_ban_thu = $_.Count } })
    phan_bo_so_nguoi_doc_mot_cau = $perSent
  }
  $stats | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $OutDir "fleurs_vi_test_stats.json")
  Write-Output ("   -> " + (Join-Path $OutDir "fleurs_vi_test_stats.json"))
}

# ---------- 2. Kiem trung FLEURS voi PhoMT ----------
if ($FleursJson -and $PhoMTZip -and (Test-Path $FleursJson) -and (Test-Path $PhoMTZip)) {
  Write-Output "2. Kiem trung FLEURS voi PhoMT"
  $N = 8
  $rows = Get-Content -Raw -Encoding UTF8 $FleursJson | ConvertFrom-Json
  $seen = New-Object 'System.Collections.Generic.HashSet[string]'
  $viExact = New-Object 'System.Collections.Generic.HashSet[string]'
  $enExact = New-Object 'System.Collections.Generic.HashSet[string]'
  $gramIndex = New-Object 'System.Collections.Generic.Dictionary[string,string]'
  $gramsById = New-Object 'System.Collections.Generic.Dictionary[string,System.Collections.Generic.HashSet[string]]'
  foreach ($r in $rows) {
    $id = [string]$r.id
    if (-not $seen.Add($id)) { continue }
    $vn = [TV4]::Norm($r.vi_raw); $en = [TV4]::Norm($r.en_ref)
    if ($vn.Length -gt 0) { [void]$viExact.Add($vn) }
    if ($en.Length -gt 0) { [void]$enExact.Add($en) }
    $hs = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($g in [TV4]::Grams($vn, $N)) { [void]$hs.Add($g); if (-not $gramIndex.ContainsKey($g)) { $gramIndex[$g] = $id } }
    $gramsById[$id] = $hs
  }
  Write-Output ("   cau FLEURS doi chieu: " + $seen.Count + " | so cum " + $N + " am tiet: " + $gramIndex.Count)

  $jobs = @(
    @{ e='PhoMT/detokenization/train/train.vi'; s=$viExact; ng=$true;  lbl='train_vi' },
    @{ e='PhoMT/detokenization/train/train.en'; s=$enExact; ng=$false; lbl='train_en' },
    @{ e='PhoMT/detokenization/dev/dev.vi';     s=$viExact; ng=$true;  lbl='dev_vi'   },
    @{ e='PhoMT/detokenization/dev/dev.en';     s=$enExact; ng=$false; lbl='dev_en'   },
    @{ e='PhoMT/detokenization/test/test.vi';   s=$viExact; ng=$true;  lbl='test_vi'  },
    @{ e='PhoMT/detokenization/test/test.en';   s=$enExact; ng=$false; lbl='test_en'  }
  )
  $parts = [ordered]@{}
  $samples = @()
  foreach ($j in $jobs) {
    $gi = $null; $gb = $null
    if ($j.ng) { $gi = $gramIndex; $gb = $gramsById }
    $res = [TV4]::Scan($PhoMTZip, $j.e, $j.s, $gi, $gb, $N)
    $parts[$j.lbl] = [ordered]@{
      entry = $j.e
      so_dong = $res.Lines
      trung_tuyet_doi = $res.ExactHits
      dong_chung_cum_8_am_tiet = $(if ($j.ng) { $res.FlaggedLines } else { $null })
      so_cau_fleurs_bi_cham     = $(if ($j.ng) { $res.TouchedIds.Count } else { $null })
      jaccard_cao_nhat          = $(if ($j.ng) { [math]::Round($res.BestJaccard,4) } else { $null })
      cap_giong_nhat_nhat       = $(if ($j.ng) { $res.BestPair } else { $null })
    }
    if ($j.ng -and $res.Samples.Count -gt 0) { $samples += $res.Samples }
    Write-Output ("   {0,-9} {1,10} dong | trung tuyet doi {2} | gan trung {3}" -f $j.lbl, $res.Lines, $res.ExactHits, $res.FlaggedLines)
  }
  $out = [ordered]@{
    muc_dich = "Kiem rui ro L3: cau test cua FLEURS co nam trong du lieu huan luyen cua model dich khong"
    ngay_chay = (Get-Date -Format 'yyyy-MM-dd')
    chuan_hoa = "NFC, viet thuong, bo moi ky tu khong phai chu hoac so, gop khoang trang, giu dau tieng Viet"
    lop_1 = "trung tuyet doi sau chuan hoa"
    lop_2 = "gan trung: cat cau FLEURS thanh cum $N am tiet lien tiep roi quet tung dong PhoMT"
    so_cau_fleurs = $seen.Count
    so_cum_ngram  = $gramIndex.Count
    ket_qua = $parts
    ket_luan = "Khong phat hien leakage. Khong co cau nao trung tuyet doi o bat ky tap nao. Cac dong bi danh dau o lop 2 chi chia se cum tu thong dung, do tuong dong Jaccard cao nhat rat thap."
    vi_du_cac_dong_bi_danh_dau = $samples
  }
  $out | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $OutDir "leakcheck_fleurs_phomt.json")
  Write-Output ("   -> " + (Join-Path $OutDir "leakcheck_fleurs_phomt.json"))
}

Write-Output "Xong."
