@echo off
echo.
echo ============================================
echo Git Branch Rename Script
echo ============================================
echo.
echo Step 1: Rename branch locally...
git branch -m agents-branch-explanation-request feature/skill-gap-bert-upgrade
echo ✓ Local rename complete
echo.

echo Step 2: Delete old remote branch...
git push origin --delete agents-branch-explanation-request
echo ✓ Old remote branch deleted
echo.

echo Step 3: Push new branch name...
git push origin feature/skill-gap-bert-upgrade
echo ✓ New branch pushed
echo.

echo Step 4: Set upstream...
git branch --set-upstream-to=origin/feature/skill-gap-bert-upgrade
echo ✓ Upstream set
echo.

echo Step 5: Verify current branch...
git branch --show-current
echo.

echo ============================================
echo ✅ Branch rename COMPLETE!
echo ============================================
echo New branch: feature/skill-gap-bert-upgrade
echo.
pause
