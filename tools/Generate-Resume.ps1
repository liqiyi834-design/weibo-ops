param(
    [Parameter(Mandatory = $true)]
    [string]$OutDir
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

function Decode-Utf8B64 {
    param([Parameter(Mandatory = $true)][string]$B64)
    $bytes = [Convert]::FromBase64String($B64)
    return [Text.Encoding]::UTF8.GetString($bytes)
}

# NOTE: Keep this script ASCII-only so Windows PowerShell does not mis-detect encoding.
$CN = @{
    name = "TEkgUVlJ"
    tagline = "MjLlsoHvvZzlpJror63oqIDvvJrkuK3mlocgLyDtlZzqta3slrQgLyBFbmdsaXNo772c5oSP5ZCR77yaT3BlblRyYWluIEFJIOWFvOiBjO+8iOi/kOiQpS/lhoXlrrkv5pWw5o2u5qCH5rOoL+i0qOajgO+8iQ=="
    contact = "6IGU57O75pa55byP77ya55S16K+d77yI5b6F6KGl77yJ772c6YKu566x77yI5b6F6KGl77yJ772c5omA5Zyo5Zyw77yI5b6F6KGl77yJ772c5L2c5ZOBL+mTvuaOpe+8iOWPr+mAie+8mkdpdEh1Yi9Ob3Rpb24v5L2c5ZOB6ZuG77yJ"

    h_highlights = "5Liq5Lq65Lqu54K5"
    hi_1 = "5b6u5Y2a54Ot54K56L+Q6JCl77ya5LuO4oCc54Ot5qac5qCH6aKY4oCd5Y2H57qn5Yiw4oCc6K+N5p2h6aG16YeH5qC34oaS5oOF57uq5YiG5q2n4oaS5Y+v5Y+R5paH5qGI4oCd55qE5bel5L2c5rWB77yM5by66LCD5LqL5a6e5qC45p+l5LiO6aOO6Zmp5YiG57qn44CC"
    hi_2 = "5pWw5o2u5YyW6YCJ6aKY77ya57u05oqkIG5ld3NfaGlzdG9yeS5jc3bvvJvnlKjnqpflj6PlpI3njrDpopHnjocr54Ot5bqm5a+55pWwK+mjjumZqeaDqee9muiuoeeul+S8mOWFiOe6p++8jOi+k+WHuiBTL0EvQiDnrYnnuqfjgII="
    hi_3 = "5bel5YW35YyW5o+Q5pWI77ya55SoIFBvd2VyU2hlbGwvSlMg5YGa6YeH5qC35a+85YWl44CB5pWw5o2u5riF5rSX44CB5oql5ZGK55Sf5oiQ77yb5bCG5pel5bi46L+Q6JCl5rKJ5reA5oiQ5Y+v5aSN55SoIFNPUCDmlofmoaPjgII="

    h_exp = "5bel5L2cL+mhueebrue7j+WOhu+8iOiKgumAie+8iQ=="
    exp_role = "5b6u5Y2a6LSm5Y+34oCc5LuK5pel5pyJ6K+d55u06K+04oCd772c5YaF5a656L+Q6JClL+aVsOaNruWMlumAiemimO+8iOS4quS6uumhueebru+8iSAgMjAyNi4wNeKAk+iHs+S7ig=="
    exp_b1 = "5Yi25a6a5q+P5pel6L+Q6JCl5rWB56iL77ya54Ot5qac562b6YCJ4oaS5YCZ6YCJ5YiG57qn4oaS6K+N5p2h6aG15qC35pys6YeH6ZuG77yI6auY6LWeL+mrmOivhC/pq5jovazlj5Ev54Ot6Zeo6K+E6K6677yJ4oaS6I2J56i/55Sf5oiQ4oaS5Y+R5biD5aSN55uY44CC"
    exp_b2 = "5rKJ5reA6aOO6Zmp5o6n5Yi25qGG5p6277ya5Lul4oCc5bey55+l5LqL5a6eL+W+heehruiupOS/oeaBry/nkIbmgKfop4Llr58v5b2x5ZON5YiG5p6QL+W8gOaUvumXrumimOKAnee7k+aehOihqOi+vu+8jOmZjeS9juS6ieiuruivnemimOeahOi/neinhOS4juivr+S8pOmjjumZqeOAgg=="
    exp_b3 = "5bu656uL5pWw5o2u5bqV5bqn77ya5Y6G5Y+y54Ot54K55Y676YeN5LiO5aSN546w57uf6K6h77yIMS8zLzcvMTUvMzAvOTAvMTgwLzM2NeWkqe+8ie+8jOaUr+aMgemrmOWkjeeOsOiurumimOaMgee7rei/vei4quOAgg=="

    proj_1 = "54Ot54K55LyY5YWI57qn566X5rOV5LiO5pel5oql55Sf5oiQ77yIUG93ZXJTaGVsbO+8iSAgMjAyNi4wNQ=="
    proj_1b = "5a6e546w54Ot5bqm6Kej5p6Q77yI5ZCr4oCc5LiH4oCd5Y2V5L2N77yJ44CB5a+55pWw54Ot5bqm5b6X5YiG44CB5aSN546w5Yqg5p2D44CB6aOO6Zmp5omj5YiG44CB562J57qn5pig5bCE77yb6L6T5Ye6IGhvdF9wcmlvcml0eV9ZWVlZLU1NLURELmNzduOAgg=="
    proj_2 = "5b6u5Y2a5Y+v6KeB5YaF5a656YeH5qC35bel5YW377yIRWRnZSBDb25zb2xlIEpT77yJICAyMDI2LjA1"
    proj_2b = "5Zyo5bey55m75b2V5rWP6KeI5Zmo5YaF5a+85Ye65Y+v6KeB5paH5pys5LiO6ZO+5o6l77yM6YG/5YWN6Kem56KwIENvb2tpZS/lr4bnoIEvVG9rZW7vvJvphY3lpZflr7zlhaXohJrmnKzlsIbmoLfmnKznu5PmnoTljJbokL3lupPjgII="

    h_skills = "5oqA6IO9"
    sk_1 = "6K+t6KiA77ya5Lit5paH77yI5q+N6K+t77yJ772c7ZWc6rWt7Ja077yI5bel5L2c5rKf6YCa77yJ772cRW5nbGlzaO+8iOW3peS9nOayn+mAmu+8iQ=="
    sk_2 = "5bel5YW377yaUG93ZXJTaGVsbOOAgUphdmFTY3JpcHTjgIFFeGNlbC9DU1bjgIHln7rnoYDmlbDmja7liIbmnpDkuI7mlofmnKzmuIXmtJc="
    sk_3 = "6IO95Yqb77ya5YaF5a65562W5YiS5LiO5YaZ5L2c44CB6IiG5oOF6KeC5a+f44CB5LqL5a6e5qC45p+l44CB6K+E6K665Yy65LqS5Yqo562W55Wl"

    h_note = "5aSH5rOo"
    note = "5pys566A5Y6G5Z+65LqO5L2g5b2T5YmN6aG555uu5LuT5bqT5YaF5a655pW055CG77yb5pyq57yW6YCg6Jma5p6E57uP5Y6G77yM5LuF5a+56KGo6L+w5YGa5LqG6IGM5Lia5YyW5LiO5oiQ5p6c5YyW44CC5oqK4oCc6IGU57O75pa55byPL+aJgOWcqOWcsC/mlZnogrLog4zmma/igJ3ooaXpvZDlkI7ljbPlj6/mipXpgJLjgII="
}

function New-ResumeDoc {
    param(
        [Parameter(Mandatory = $true)][string]$DocxPath,
        [Parameter(Mandatory = $true)][string]$PdfPath,
        [Parameter(Mandatory = $true)][ValidateSet("CN", "EN")][string]$Lang
    )

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    $doc = $word.Documents.Add()
    $doc.PageSetup.PaperSize = 7 # A4
    $doc.PageSetup.TopMargin = $word.CentimetersToPoints(1.6)
    $doc.PageSetup.BottomMargin = $word.CentimetersToPoints(1.6)
    $doc.PageSetup.LeftMargin = $word.CentimetersToPoints(1.7)
    $doc.PageSetup.RightMargin = $word.CentimetersToPoints(1.7)

    $doc.Styles.Item("Normal").Font.Name = "Calibri"
    $doc.Styles.Item("Normal").Font.Size = 10.5

    function Add-Para([string]$Text, [double]$Size, [bool]$Bold, [double]$SpaceAfter, [string]$FontName) {
        $p = $doc.Content.Paragraphs.Add()
        $p.Range.Text = $Text
        if (-not [string]::IsNullOrWhiteSpace($FontName)) { $p.Range.Font.Name = $FontName }
        $p.Range.Font.Size = $Size
        $p.Range.Font.Bold = [int]$Bold
        $p.Format.SpaceAfter = $SpaceAfter
        $null = $p.Range.InsertParagraphAfter()
    }

    function Add-Heading([string]$Text) { Add-Para $Text 12 $true 6 "" }

    function Add-Bullet([string]$Text) {
        $p = $doc.Content.Paragraphs.Add()
        $p.Range.Text = $Text
        $p.Range.Font.Size = 10.5
        $p.Range.Font.Bold = 0
        $p.Range.ListFormat.ApplyBulletDefault()
        $p.Format.SpaceAfter = 2
        $null = $p.Range.InsertParagraphAfter()
    }

    if ($Lang -eq "CN") {
        Add-Para (Decode-Utf8B64 $CN.name) 20 $true 2 "Calibri"
        Add-Para (Decode-Utf8B64 $CN.tagline) 10.5 $false 8 "Microsoft YaHei"
        Add-Para (Decode-Utf8B64 $CN.contact) 9.5 $false 10 "Microsoft YaHei"

        Add-Heading (Decode-Utf8B64 $CN.h_highlights)
        Add-Bullet (Decode-Utf8B64 $CN.hi_1)
        Add-Bullet (Decode-Utf8B64 $CN.hi_2)
        Add-Bullet (Decode-Utf8B64 $CN.hi_3)

        Add-Heading (Decode-Utf8B64 $CN.h_exp)
        Add-Para (Decode-Utf8B64 $CN.exp_role) 10.5 $true 4 "Microsoft YaHei"
        Add-Bullet (Decode-Utf8B64 $CN.exp_b1)
        Add-Bullet (Decode-Utf8B64 $CN.exp_b2)
        Add-Bullet (Decode-Utf8B64 $CN.exp_b3)

        Add-Para (Decode-Utf8B64 $CN.proj_1) 10.5 $true 4 "Microsoft YaHei"
        Add-Bullet (Decode-Utf8B64 $CN.proj_1b)
        Add-Para (Decode-Utf8B64 $CN.proj_2) 10.5 $true 4 "Microsoft YaHei"
        Add-Bullet (Decode-Utf8B64 $CN.proj_2b)

        Add-Heading (Decode-Utf8B64 $CN.h_skills)
        Add-Bullet (Decode-Utf8B64 $CN.sk_1)
        Add-Bullet (Decode-Utf8B64 $CN.sk_2)
        Add-Bullet (Decode-Utf8B64 $CN.sk_3)

        Add-Heading (Decode-Utf8B64 $CN.h_note)
        Add-Para (Decode-Utf8B64 $CN.note) 9.5 $false 0 "Microsoft YaHei"
    } else {
        Add-Para "LI QYI" 20 $true 2 "Calibri"
        Add-Para "Age 22 | Languages: Chinese / Korean / English | Target: Part-time at OpenTrain AI (Ops / Content / Data QA)" 10.5 $false 8 "Calibri"
        Add-Para "Contact: Phone (TBD) | Email (TBD) | Location (TBD) | Portfolio/Links (optional)" 9.5 $false 10 "Calibri"

        Add-Heading "Highlights"
        Add-Bullet "Weibo trend operations: moved from title-based posts to topic-page sampling, sentiment splits, and publish-ready copy, with fact-checking and risk grading."
        Add-Bullet "Data-driven topic prioritization: maintained a news history log and built a recurrence/heat/risk scoring model to rank S/A candidates."
        Add-Bullet "Workflow automation: PowerShell/JS scripts for sample ingestion, cleaning, and reporting; converted daily ops into reusable SOPs."

        Add-Heading "Experience and Projects (Selected)"
        Add-Para "Weibo account \"Today, Speak Frankly\" | Content Ops and Topic Intelligence (Personal Project)  May 2026 - Present" 10.5 $true 4 "Calibri"
        Add-Bullet "Designed a daily loop: hotlist scan, candidate grading, topic-page sampling (top-liked/top-commented/top-reposted plus hot comments), draft generation, and post-mortem review."
        Add-Bullet "Applied a safe-structure writing framework (known facts / to-verify / rational observation / impact analysis / open questions) to reduce compliance risk on controversial topics."
        Add-Bullet "Built a lightweight data layer with dedup and recurrence windows (1/3/7/15/30/90/180/365 days) to track high-recurrence storylines."

        Add-Para "Hot Topic Priority Scoring and Daily Report (PowerShell)  May 2026" 10.5 $true 4 "Calibri"
        Add-Bullet "Implemented hot-value parsing (including 10k-unit), log-based heat scoring, recurrence weighting, risk penalties, and level mapping; exported a daily CSV priority report."

        Add-Para "Visible-Page Weibo Sampler (Edge Console JS)  May 2026" 10.5 $true 4 "Calibri"
        Add-Bullet "Exported only visible DOM text and links from a logged-in browser session (no cookies/tokens); paired with an import script to structure samples into CSV."

        Add-Heading "Skills"
        Add-Bullet "Languages: Chinese (native) | Korean (professional) | English (professional)"
        Add-Bullet "Tools: PowerShell, JavaScript, Excel/CSV, basic text/data cleaning"
        Add-Bullet "Strengths: content planning and writing, sentiment observation, lightweight fact-checking, comment engagement strategy"

        Add-Heading "Note"
        Add-Para "Compiled from your existing local project artifacts. I did not fabricate employers or credentials; wording is optimized for clarity and impact. Add education/contact details before applying." 9.5 $false 0 "Calibri"
    }

    foreach ($p in @($DocxPath, $PdfPath)) {
        if (Test-Path $p) { Remove-Item -LiteralPath $p -Force }
    }

    $doc.SaveAs([ref]$DocxPath, [ref]16) | Out-Null
    $doc.ExportAsFixedFormat($PdfPath, 17) | Out-Null

    $doc.Close()
    $word.Quit()
}

$cnDocx = Join-Path $OutDir "LI_QYI_Resume_CN.docx"
$cnPdf = Join-Path $OutDir "LI_QYI_Resume_CN.pdf"
$enDocx = Join-Path $OutDir "LI_QYI_Resume_EN.docx"
$enPdf = Join-Path $OutDir "LI_QYI_Resume_EN.pdf"

New-ResumeDoc -DocxPath $cnDocx -PdfPath $cnPdf -Lang "CN"
New-ResumeDoc -DocxPath $enDocx -PdfPath $enPdf -Lang "EN"

Write-Host ("Wrote: " + $cnPdf)
Write-Host ("Wrote: " + $enPdf)
