@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM ---------------------------------------------------------------------------
REM  Tim Python. Thu tu nay co ly do:
REM   1) `py -3`  : launcher cua python.org, nam o C:\Windows nen chay duoc NGAY
REM                 CA KHI nguoi dung quen tich "Add to PATH" luc cai - truong
REM                 hop rat pho bien. No cung KHONG BAO GIO trung ban gia lap
REM                 cua Microsoft Store.
REM   2) `python` : chi dung khi (1) that bai.
REM
REM  KHONG dung `where ... | find "WindowsApps"` de loc ban gia lap. Da thu va
REM  no SAI hai duong: (a) `where python` liet ke CA ban that lan ban gia lap,
REM  nen loc theo chuoi se ket luan "khong co Python" tren may VAN CO Python;
REM  (b) `find` co the bi chuong trinh khac (Git Bash) che mat, luc do lenh loi
REM  va chot chan im lang khong chay. Phep thu phien ban ben duoi da du: ban
REM  gia lap khong chay duoc Python nen tu no truot.
REM ---------------------------------------------------------------------------
set "PY="
REM ---------------------------------------------------------------------------
REM  File cua tool con du khong? Kiem TRUOC khi dung den Python (bug #89).
REM  Thu tu nay QUAN TRONG. Neu kiem Python truoc: thieu `chung.py` se lam
REM  phep kiem ban di kem (`import sys,chung`) truot, va tren may KHONG co
REM  Python he thong thi ca ba ung vien deu truot -> .bat ket luan "may nay
REM  chua co Python" - SAI. Nguoi dung di cai Python roi quay lai van hong.
REM  `if not exist` khong can interpreter va khong the hieu sai.
REM ---------------------------------------------------------------------------
set "THIEU="
if not exist "%~dp0goi_project_capcut.py" set "THIEU=%THIEU% goi_project_capcut.py"
if not exist "%~dp0chung.py" set "THIEU=%THIEU% chung.py"
if not "%THIEU%"=="" goto :thieu_file

REM ---------------------------------------------------------------------------
REM  0) Ban Python DI KEM trong `python\`. Uu tien tuyet doi:
REM     - khong can cai dat, khong can quyen admin
REM     - khong dung toi PATH hay Python san co cua may con
REM     - moi may chay DUNG MOT phien ban giong may cha (3.14.6)
REM  Kiem bang cach `import chung` chu KHONG phai `if exist python.exe`:
REM  file co mat khong co nghia la chay duoc (bai hoc #72). Mot lenh nay kiem
REM  dong thoi: interpreter song, DLL du, file ._pth dung, phien ban du.
REM ---------------------------------------------------------------------------
if not exist "%~dp0python\python.exe" goto :thu_he_thong
"%~dp0python\python.exe" -c "import sys,chung;raise SystemExit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if not errorlevel 1 set "PY="%~dp0python\python.exe""
if defined PY goto :co_python
echo.
echo   ! Ban Python di kem trong thu muc `python\` KHONG chay duoc.
echo     Co the giai nen bi thieu file, hoac bi phan mem bao ve chan.
echo     Dang thu Python cua may...
echo.

:thu_he_thong
py -3 -c "import sys;raise SystemExit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :co_python

python -c "import sys;raise SystemExit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto :co_python

goto :thieu_python

:thieu_python
echo.
echo ================================================================
echo   KHONG CHAY DUOC - may nay chua co Python 3.8 tro len
echo ================================================================
echo.
echo   Cach sua (lam MOT LAN, khoang 3 phut):
echo.
echo     1. Mo trinh duyet, vao:  https://www.python.org/downloads/
echo     2. Bam nut vang "Download Python" de tai ban moi nhat
echo     3. Chay file vua tai. QUAN TRONG: o DAY man hinh dau tien,
echo        TICH VAO O  [x] Add python.exe to PATH
echo        roi moi bam "Install Now".
echo     4. Cai xong: DONG cua so nay lai, roi bam dup lai file .bat
echo.
echo   Neu bam dup ma Windows mo Microsoft Store: do la ban gia lap
echo   cua Windows, khong dung duoc. Hay cai tu python.org nhu tren.
echo.
goto :xong

:co_python
REM ---------------------------------------------------------------------------
REM  KHONG dung khoi `if ... ( ... )` o day, va PHAI boc `%~dp0` trong ngoac kep.
REM  Da do that: thu muc ten `goi_project_capcut (1)` - chinh la ten Windows TU
REM  DAT khi giai nen zip lan thu hai vao cung cho - lam ca file .bat vo:
REM      dau `)` trong duong dan DONG KHOI SOM  -> `\ was unexpected at this time.`
REM      dau `&` trong duong dan TACH LENH      -> `'...thu' is not recognized`
REM  Nang hon nua: cmd.exe phan tich CA KHOI truoc khi chay, nen tool khong khoi
REM  dong duoc NGAY CA KHI day du file. Dung `goto` + ngoac kep thi het ca hai.
REM ---------------------------------------------------------------------------
if exist "%~dp0goi_project_capcut.py" goto :chay
echo.
echo ================================================================
echo   KHONG CHAY DUOC - thieu file goi_project_capcut.py
echo ================================================================
echo.
echo   Thu muc nay:
echo   "%~dp0"
echo   Hay chep LAI CA THU MUC cong cu sang may nay,
echo   dung chep rieng tung file.
echo.
goto :xong

:chay
%PY% "%~dp0goi_project_capcut.py"

:thieu_file
echo.
echo ================================================================
echo   KHONG CHAY DUOC - GIAI NEN THIEU FILE
echo ================================================================
echo.
echo   Thieu file:%THIEU%
echo.
echo   Thu muc dang chay:
echo   "%~dp0"
echo.
echo   Cach sua: GIAI NEN LAI ca file zip vao mot thu muc trong.
echo   Neu ban chep tu may khac sang, hay chep CA THU MUC cong cu,
echo   dung chep rieng tung file.
echo.
echo   (Day KHONG phai loi Python - khong can cai gi ca.)
echo.
goto :xong

:xong
echo.
pause
