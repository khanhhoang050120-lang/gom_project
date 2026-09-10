@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM ===========================================================================
REM  GIAO DIEN - bam dup file nay.
REM
REM  Cua so den (console) nay CHI hien trong luc kiem (~1 giay) roi tu dong bien
REM  mat. Giao dien chay bang `pythonw.exe` nen KHONG kem console.
REM
REM  Vi sao khong an console ngay tu dau: khi do moi loi khoi dong (thieu file,
REM  Python hong, tkinter hong) deu IM LANG - nguoi dung bam dup ma khong thay
REM  gi xay ra, khong biet phai lam sao. Giu console trong pha kiem la de nhung
REM  loi do van noi duoc ra.
REM ===========================================================================
set "PY="
set "PYW="

REM --- 1) File cua tool con du khong? Kiem TRUOC khi dung den Python. --------
REM  Thu tu nay QUAN TRONG (bug #89). Neu kiem Python truoc: thieu `chung.py`
REM  se lam moi phep kiem Python that bai, va .bat ket luan "may chua co
REM  Python" - sai. Nguoi dung di cai Python roi van hong.
REM
REM  Chi liet ke nhung file MA THIEU LA KHONG THE HIEN NOI CUA SO NAO: chung
REM  deu duoc `giao_dien.py` nap ngay luc import, duoi `pythonw` thi loi do
REM  khong co cho nao hien ra. Cac file con lai (cau_hinh.json, ffmpeg...) do
REM  CUA SO TU KIEM bao - no giai thich ro rang hon nhieu so voi console.
set "THIEU="
if not exist "%~dp0giao_dien.py" set "THIEU=%THIEU% giao_dien.py"
if not exist "%~dp0goi_project_capcut.py" set "THIEU=%THIEU% goi_project_capcut.py"
if not exist "%~dp0chung.py" set "THIEU=%THIEU% chung.py"
if not exist "%~dp0tu_kiem_lan_dau.py" set "THIEU=%THIEU% tu_kiem_lan_dau.py"
if not "%THIEU%"=="" goto :thieu_file

REM --- 2) Ban Python DI KEM: khong can cai, khong can admin, khong dung PATH -
REM  Kiem bang `import giao_dien` chu KHONG phai `if exist python.exe`: file co
REM  mat khong co nghia la chay duoc (bai hoc #72). Mot lenh nay kiem cung luc:
REM  interpreter song, DLL du, ._pth dung, phien ban du, tkinter dung duoc, VA
REM  ca chuoi import cua giao dien - dung chuoi se chay duoi `pythonw`.
if not exist "%~dp0python\python.exe" goto :thu_he_thong
"%~dp0python\python.exe" -c "import sys;sys.path.insert(0,'.');import giao_dien;raise SystemExit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if errorlevel 1 goto :di_kem_hong
set "PY="%~dp0python\python.exe""
set "PYW="%~dp0python\pythonw.exe""
if not exist "%~dp0python\pythonw.exe" set "PYW=%PY%"
goto :chay

:di_kem_hong
echo.
echo   ! Ban Python di kem trong thu muc `python\` KHONG dung duoc cho giao dien.
echo     Co the giai nen bi thieu file, hoac bi phan mem bao ve chan.
echo     Dang thu Python cua may...
echo.

:thu_he_thong
py -3 -c "import sys;sys.path.insert(0,'.');import giao_dien;raise SystemExit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if errorlevel 1 goto :thu_python
set "PY=py -3"
set "PYW=pyw -3"
goto :chay

:thu_python
python -c "import sys;sys.path.insert(0,'.');import giao_dien;raise SystemExit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if errorlevel 1 goto :khong_chay_duoc
set "PY=python"
set "PYW=pythonw"
goto :chay

:khong_chay_duoc
echo.
echo ================================================================
echo   KHONG CHAY DUOC GIAO DIEN
echo ================================================================
echo.
echo   Loi that (dong CUOI CUNG thuong noi ro nguyen nhan):
echo   ----------------------------------------------------------------
REM  In loi THAT thay vi doan. Neu chi in loi khuyen chung chung thi khi
REM  nguyen nhan la thu khac (file hong, phan mem bao ve chan DLL...) nguoi
REM  dung se lam theo huong dan sai va van hong.
if not exist "%~dp0python\python.exe" goto :in_loi_he_thong
"%~dp0python\python.exe" -c "import sys;sys.path.insert(0,'.');import giao_dien" 2>&1
goto :da_in_loi
:in_loi_he_thong
py -3 -c "import sys;sys.path.insert(0,'.');import giao_dien" 2>&1
:da_in_loi
echo   ----------------------------------------------------------------
echo.
echo   Neu dong cuoi noi `ModuleNotFoundError` hoac `ImportError`:
echo     -^> Giai nen bi thieu file. Hay GIAI NEN LAI ca file zip.
echo.
echo   Neu dong cuoi nhac den `tkinter` hoac `_tkinter`:
echo     -^> Python tren may nay thieu phan giao dien. Cai lai Python tu
echo        https://www.python.org/downloads/ - o man hinh dau tien nho
echo        TICH VAO O  [x] Add python.exe to PATH  roi bam "Install Now".
echo        Neu bam dup ma Windows mo Microsoft Store: do la ban gia lap,
echo        khong dung duoc. Hay cai tu python.org.
echo.
echo   Neu khong co dong nao o tren (hoac bao 'is not recognized'):
echo     -^> May nay chua co Python 3.8 tro len. Cai theo dia chi tren.
echo.
echo   Van con cach khac: bam dup `goi_project_capcut.bat` de chay ban
echo   DONG LENH (khong can tkinter).
echo.
goto :xong

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

:chay
REM  KHONG dung khoi `if ... ( ... )`, va PHAI boc `%~dp0` trong ngoac kep:
REM  thu muc ten `goi_project_capcut (1)` - ten Windows TU DAT khi giai nen zip
REM  lan hai - lam vo ca file .bat (bug #73).
REM
REM  `start ""` tach han tien trinh ra; `.bat` thoat ngay sau do nen console
REM  bien mat. `pythonw.exe` khong tao console moi -> chi con cua so giao dien.
start "" %PYW% "%~dp0giao_dien.py"
exit /b 0

:xong
echo.
pause
exit /b 1
