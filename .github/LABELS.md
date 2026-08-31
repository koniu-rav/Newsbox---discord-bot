# GitHub Labels & Issue Management Guide

This document describes the repository's standard issue classification and label scheme.

---

## 📋 Ticket Types & Templates

| Type | Label | Template File | Purpose |
| :--- | :---- | :------------ | :------ |
| **User Story** | `type: user-story` | `.github/ISSUE_TEMPLATE/user_story.yml` | Features, enhancements, and user capabilities with Acceptance Criteria & Design specs |
| **Bug** | `type: bug` | `.github/ISSUE_TEMPLATE/bug_report.yml` | Defect reports with Reproduction Steps, Current vs Expected results |
| **Tech Story** | `type: tech-story` | `.github/ISSUE_TEMPLATE/tech_story.yml` | Internal engineering, refactoring, technical debt, and infra improvements |

---

## 🏷️ Standard Labels Catalog

### Issue Types
- `type: user-story` (`#0052cc`): User-facing feature or enhancement with acceptance criteria
- `type: bug` (`#d73a4a`): Something isn't working as expected
- `type: tech-story` (`#5319e7`): Internal technical task, refactoring, or architectural improvement
- `type: documentation` (`#0075ca`): Improvements or additions to documentation

### Priorities
- `priority: high` (`#b60205`): Urgent issue requiring immediate attention
- `priority: medium` (`#fbca04`): Normal priority task scheduled in current cycle
- `priority: low` (`#0e8a16`): Low priority or nice-to-have improvement

### Components
- `component: discord-bot` (`#7289da`): Discord.py cogs, commands, and interaction handlers
- `component: gemini-ai` (`#4285f4`): Google Gemini API prompt engineering and summarization
- `component: market-data` (`#1d76db`): Financial feeds for DXY, EUR/USD, DAX, and BTC
- `component: economic-calendar` (`#0e8a16`): Macroeconomic event fetcher and calendar sync
- `component: scheduler` (`#d4c5f9`): Daily 8:00 AM briefing scheduling and cron dispatch

---

## 🚀 Quick Setup with GitHub CLI (`gh`)

To synchronize or apply all labels to the GitHub repository using the GitHub CLI:

```bash
# Set up labels in GitHub repository
gh label create "type: user-story" --color "0052cc" --description "User-facing feature with acceptance criteria" --force
gh label create "type: bug" --color "d73a4a" --description "Something isn't working as expected" --force
gh label create "type: tech-story" --color "5319e7" --description "Internal technical task or refactoring" --force
gh label create "priority: high" --color "b60205" --description "Urgent issue requiring immediate attention" --force
gh label create "priority: medium" --color "fbca04" --description "Normal priority task" --force
gh label create "priority: low" --color "0e8a16" --description "Low priority improvement" --force
gh label create "component: discord-bot" --color "7289da" --description "Discord.py cogs and commands" --force
gh label create "component: gemini-ai" --color "4285f4" --description "Google Gemini API integrations" --force
gh label create "component: market-data" --color "1d76db" --description "Market tickers (DXY, EUR/USD, DAX, BTC)" --force
gh label create "component: economic-calendar" --color "0e8a16" --description "Economic calendar event fetcher" --force
gh label create "component: scheduler" --color "d4c5f9" --description "Daily briefing dispatch scheduler" --force
```

