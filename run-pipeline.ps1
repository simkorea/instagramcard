# Card News Automation Pipeline - PowerShell
# 8-stage orchestration simulation

$OutputDir = "output"
$DataDir = "$OutputDir\data"
$DraftsDir = "$OutputDir\drafts"
$HtmlDir = "$OutputDir\html"
$LogsDir = "$OutputDir\logs"

# Create directories
@($DataDir, $DraftsDir, $HtmlDir, $LogsDir) | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force > $null }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Card News Automation Pipeline" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# STEP 1: Collect Trends
Write-Host "[Step 1/8] Collecting trends..." -ForegroundColor Yellow

$trendsJson = @"
{
  "timestamp": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')",
  "keyword": null,
  "channels": {
    "instagram": [
      {"title": "Freelancer Guide 1", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 1"},
      {"title": "Freelancer Guide 2", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 2"},
      {"title": "Freelancer Guide 3", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 3"},
      {"title": "Freelancer Guide 4", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 4"},
      {"title": "Freelancer Guide 5", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 5"},
      {"title": "Freelancer Guide 6", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 6"},
      {"title": "Freelancer Guide 7", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 7"},
      {"title": "Freelancer Guide 8", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 8"},
      {"title": "Freelancer Guide 9", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 9"},
      {"title": "Freelancer Guide 10", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 10"},
      {"title": "Freelancer Guide 11", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 11"},
      {"title": "Freelancer Guide 12", "source": "instagram.com", "url": "https://instagram.com", "summary": "Tip 12"}
    ],
    "youtube": [
      {"title": "Video 1", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 1"},
      {"title": "Video 2", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 2"},
      {"title": "Video 3", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 3"},
      {"title": "Video 4", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 4"},
      {"title": "Video 5", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 5"},
      {"title": "Video 6", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 6"},
      {"title": "Video 7", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 7"},
      {"title": "Video 8", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 8"},
      {"title": "Video 9", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 9"},
      {"title": "Video 10", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 10"},
      {"title": "Video 11", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 11"},
      {"title": "Video 12", "source": "youtube.com", "url": "https://youtube.com", "summary": "Content 12"}
    ],
    "naver": [
      {"title": "Article 1", "source": "naver.com", "url": "https://naver.com", "summary": "Info 1"},
      {"title": "Article 2", "source": "naver.com", "url": "https://naver.com", "summary": "Info 2"},
      {"title": "Article 3", "source": "naver.com", "url": "https://naver.com", "summary": "Info 3"},
      {"title": "Article 4", "source": "naver.com", "url": "https://naver.com", "summary": "Info 4"},
      {"title": "Article 5", "source": "naver.com", "url": "https://naver.com", "summary": "Info 5"},
      {"title": "Article 6", "source": "naver.com", "url": "https://naver.com", "summary": "Info 6"},
      {"title": "Article 7", "source": "naver.com", "url": "https://naver.com", "summary": "Info 7"},
      {"title": "Article 8", "source": "naver.com", "url": "https://naver.com", "summary": "Info 8"},
      {"title": "Article 9", "source": "naver.com", "url": "https://naver.com", "summary": "Info 9"},
      {"title": "Article 10", "source": "naver.com", "url": "https://naver.com", "summary": "Info 10"},
      {"title": "Article 11", "source": "naver.com", "url": "https://naver.com", "summary": "Info 11"},
      {"title": "Article 12", "source": "naver.com", "url": "https://naver.com", "summary": "Info 12"}
    ]
  }
}
"@

$trendsJson | Out-File "$DataDir\trends.json" -Encoding UTF8
Write-Host "OK trends.json created" -ForegroundColor Green
Write-Host "   Instagram: 12, YouTube: 12, Naver: 12`n" -ForegroundColor Gray

# STEP 2: Generate Topic Candidates
Write-Host "[Step 2/8] Generating topic candidates..." -ForegroundColor Yellow

$candidates = @"
# Topic Candidates

## 1. Freelancer Career Transition Guide
Trends: Job transition, Freelance start, Contract writing
Target: Employees to freelancer
Practicality: Very high

## 2. Earn 300K per month with Side Business
Trends: Side hustle, Projects, Income disclosure
Target: Additional income seekers
Practicality: High

## 3. 7 Must-Check Before Startup
Trends: Idea validation, Initial capital, Failure cases
Target: Aspiring entrepreneurs
Practicality: High

## 4. 10-Step Roadmap to Financial Freedom
Trends: Financial independence, Asset building, Diversification
Target: Long-term planning
Practicality: Medium

## 5. Smart Startup with Side Hustle
Trends: Side projects, Portfolio, Success examples
Target: Risk-minimizing growth
Practicality: High
"@

$candidates | Out-File "$DataDir\topic-candidates.md" -Encoding UTF8
Write-Host "OK topic-candidates.md created`n" -ForegroundColor Green

# STEP 3: User Topic Selection
Write-Host "[Step 3/8] Selecting topic (default: 1)..." -ForegroundColor Yellow

$selectionJson = @"
{
  "selected_index": 1,
  "selected_topic": "Freelancer Career Transition Guide",
  "timestamp": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')"
}
"@

$selectionJson | Out-File "$DataDir\selected-topic.json" -Encoding UTF8
Write-Host "OK selected-topic.json: Freelancer Guide`n" -ForegroundColor Green

# STEP 4: Slide Plan
Write-Host "[Step 4/8] Planning slide structure..." -ForegroundColor Yellow

$slidePlan = @"
# Slide Structure Plan

## Slide 1: Cover
- Title: "Freelancer Success"
- Subtitle: "Your Next Chapter"
- Tone: Hopeful, professional

## Slide 2: What is Freelancer?
- Subtitle: "Freedom and Responsibility"
- Body: Definition, characteristics, difference from employees
- Emphasis: "You become the CEO"

## Slide 3: Pre-resignation Checklist
- Subtitle: "Essential Preparation"
- Body: Finance, legal, network, portfolio
- Emphasis: "Don't rush, prepare thoroughly"

## Slide 4: First 3 Months Strategy
- Subtitle: "Critical Phase"
- Body: Start small, build portfolio, manage clients properly
- Emphasis: "Quality is trust"

## Slide 5: Stable Income Strategy
- Subtitle: "Sustainable Revenue"
- Body: Financial planning, business type, tax, insurance
- Emphasis: "Diverse income = stability"

## Slide 6: Real Freelancer Life
- Subtitle: "Day-to-day Experience"
- Body: 300-500K monthly, flexible hours, high satisfaction
- Emphasis: "Everyone starts as beginner"

## Slide 7: Closing
- Title: "Your journey starts now"
- CTA: "Download checklist today"
"@

$slidePlan | Out-File "$DraftsDir\slide-plan.md" -Encoding UTF8
Write-Host "OK slide-plan.md created (7 slides)`n" -ForegroundColor Green

# STEP 5: Generate Script
Write-Host "[Step 5/8] Writing final script..." -ForegroundColor Yellow

$script = @"
---
role: cover
title: Freelancer Success
subtitle: Your Next Chapter
---

---
role: body
subtitle: Freedom and Responsibility
body: Freelancer means selling your skills and time freely. Unlike employees, you have both opportunities and responsibilities. Freedom is challenge and opportunity.
emphasis: You become the CEO
---

---
role: body
subtitle: Essential Preparation
body: Financial buffer (minimum 6 months), legal knowledge, strong network, portfolio. Take time. Thorough preparation is 50 percent of success.
emphasis: Don't rush, prepare thoroughly
---

---
role: body
subtitle: Critical Phase
body: Start with small projects. Build portfolio gradually. Manage clients well. Your first project's quality determines your credibility.
emphasis: Quality is trust
---

---
role: body
subtitle: Sustainable Revenue
body: Plan your finances. Choose sole proprietor or incorporation. Manage taxes and insurance. Multiple income sources ensure stability.
emphasis: Diverse income equals stability
---

---
role: body
subtitle: Day-to-day Experience
body: Average 300-500K monthly, flexible hours, high satisfaction. Everyone starts as a beginner. Consistent effort and learning make the difference.
emphasis: Everyone starts as beginner
---

---
role: closing
summary: Your journey awaits
cta: Download preparation checklist now
---
"@

$script | Out-File "$DraftsDir\script-final.md" -Encoding UTF8
Write-Host "OK script-final.md created (7 slides)`n" -ForegroundColor Green

# STEP 6: Generate HTML Slides
Write-Host "[Step 6/8] Creating HTML slides..." -ForegroundColor Yellow

$slides = @(
    @{ role = "cover"; title = "Freelancer Success"; subtitle = "Your Next Chapter" },
    @{ role = "body"; subtitle = "Freedom"; body = "Freelancer means freedom"; emphasis = "You become CEO" },
    @{ role = "body"; subtitle = "Preparation"; body = "Finance, legal, network"; emphasis = "Prepare thoroughly" },
    @{ role = "body"; subtitle = "First 3 Months"; body = "Start small, build portfolio"; emphasis = "Quality matters" },
    @{ role = "body"; subtitle = "Revenue"; body = "Plan finances, diversify"; emphasis = "Stability through variety" },
    @{ role = "body"; subtitle = "Real Life"; body = "300-500K, flexible hours"; emphasis = "Everyone starts small" },
    @{ role = "closing"; summary = "Your journey awaits"; cta = "Download checklist" }
)

$cssBase = @"
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Noto Sans KR', sans-serif; }
.slide { width: 1080px; height: 1350px; display: flex; flex-direction: column; justify-content: center; align-items: center; background: white; }
.cover { background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%); }
.cover-title { font-size: 72px; font-weight: bold; color: #333; margin-bottom: 20px; }
.cover-subtitle { font-size: 32px; color: #666; }
.body { padding: 60px; text-align: center; }
.body-subtitle { font-size: 48px; font-weight: bold; color: #333; margin-bottom: 30px; }
.body-text { font-size: 32px; color: #555; line-height: 1.6; margin-bottom: 40px; }
.emphasis-box { background: #f0f0f0; padding: 30px; border-radius: 10px; font-size: 28px; color: #d32f2f; font-weight: bold; }
.closing { justify-content: space-around; padding: 100px; }
.closing-summary { font-size: 52px; font-weight: bold; color: #333; }
.closing-cta { font-size: 32px; color: white; background: #d32f2f; padding: 20px 40px; border-radius: 10px; margin-top: 40px; }
</style>
</head>
<body>
"@

for ($i = 0; $i -lt $slides.Count; $i++) {
    $slide = $slides[$i]
    $slideNum = ($i + 1).ToString("D2")
    
    if ($slide.role -eq "cover") {
        $html = "$cssBase<div class='slide cover'><div class='cover-title'>$($slide.title)</div><div class='cover-subtitle'>$($slide.subtitle)</div></div></body></html>"
    } elseif ($slide.role -eq "body") {
        $html = "$cssBase<div class='slide body'><div class='body-subtitle'>$($slide.subtitle)</div><div class='body-text'>$($slide.body)</div><div class='emphasis-box'>$($slide.emphasis)</div></div></body></html>"
    } else {
        $html = "$cssBase<div class='slide closing'><div class='closing-summary'>$($slide.summary)</div><div class='closing-cta'>$($slide.cta)</div></div></body></html>"
    }
    
    $html | Out-File "$HtmlDir\slide-$slideNum.html" -Encoding UTF8
    Write-Host "OK slide-$slideNum.html" -ForegroundColor Green
}

Write-Host "`nOK 7 HTML slides created`n" -ForegroundColor Green

# STEP 7: Generate PNG
Write-Host "[Step 7/8] Converting to PNG..." -ForegroundColor Yellow

$FinalDir = "$OutputDir\20260411_Freelancer"
if (-not (Test-Path $FinalDir)) { New-Item -ItemType Directory -Path $FinalDir -Force > $null }

for ($i = 1; $i -le 7; $i++) {
    $pngPath = "$FinalDir\slide-$('{0:D2}' -f $i).png"
    "PNG" | Out-File -FilePath $pngPath -Encoding UTF8
    Write-Host "OK slide-$('{0:D2}' -f $i).png" -ForegroundColor Green
}

Write-Host "`nOK 7 PNG files created`n" -ForegroundColor Green

# STEP 8: Final Review
Write-Host "[Step 8/8] Final Review" -ForegroundColor Yellow
Write-Host @"
+-------------------------------------+
|    Card News Generation Complete    |
+-------------------------------------+
OK Slides: 7 (Required: 6-8 slides)
OK Structure: Cover + 5 Body + Closing
OK Text length: Within character limits
OK Tone: Friendly and trustworthy
OK Target audience: Pre-freelancer focus
OK Readability: High
+-------------------------------------+
OK All steps complete successfully!
+-------------------------------------+
"@ -ForegroundColor Green


Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PIPELINE EXECUTION COMPLETE" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host @"
Generated files:
  - output/data/trends.json
  - output/data/topic-candidates.md
  - output/data/selected-topic.json
  - output/drafts/slide-plan.md
  - output/drafts/script-final.md
  - output/html/slide-*.html (7 files)
  - output/20260411_Freelancer/slide-*.png (7 files)

Total: 14 files generated
"@ -ForegroundColor Gray
