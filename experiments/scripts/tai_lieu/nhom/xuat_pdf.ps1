# Xuất PDF từ Word/PowerPoint và PNG từng slide để kiểm bố cục.
$O = "D:\CAIDCM\teamwork\tai_lieu_nhom_V2"
$w = New-Object -ComObject Word.Application; $w.Visible = $false
foreach ($f in "1_bao_cao\BaoCao_Project_Nhom", "3_paper\Paper_Springer_LNCS", "4_checklist\Checklist_Nop_Bai") {
    $d = $w.Documents.Open("$O\$f.docx", $false, $true)
    $d.ExportAsFixedFormat("$O\$f.pdf", 17)
    "$f : $($d.ComputeStatistics(2)) trang"
    $d.Close(0)
}
$w.Quit()
$p = New-Object -ComObject PowerPoint.Application
$s = $p.Presentations.Open("$O\2_slide\Slide_Project_Nhom.pptx", -1, 0, 0)
$s.SaveAs("$O\2_slide\Slide_Project_Nhom.pdf", 32)
New-Item -ItemType Directory -Force "$O\2_slide\_png" | Out-Null
$s.Export("$O\2_slide\_png", "PNG", 1600, 900)
"slide: $($s.Slides.Count)"
$s.Close(); $p.Quit()
