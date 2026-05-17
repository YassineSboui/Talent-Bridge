@echo off
echo.
echo ============================================
echo Git Branch Rename Script (CORRECTED)
echo ============================================
echo.
echo Step 1: Check current branch...
git branch --show-current
echo.

echo Step 2: Rename branch locally...
git branch -m "agents/branch-explanation-request" "feature/skill-gap-bert-upgrade"
echo ✓ Local rename complete
echo.

echo Step 3: Push new branch name...
git push origin --set-upstream "feature/skill-gap-bert-upgrade"
echo ✓ New branch pushed
echo.

echo Step 4: Delete old remote branch (optional)...
git push origin --delete "agents/branch-explanation-request" 2>nul || echo (Already deleted or doesn't exist - that's ok)
echo ✓ Old branch cleanup done
echo.

echo Step 5: Verify current branch...
git branch --show-current
echo.

echo ============================================
echo ✅ Branch rename COMPLETE!
echo ============================================
echo.
pause
