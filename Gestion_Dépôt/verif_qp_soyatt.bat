@echo off
chcp 65001 >nul
cd /d "E:\Projet Site\SANKE\SGDS\Gestion_Dépôt"
echo Activation du venv...
call ..\env\Scripts\activate.bat
echo Calcul QP Coulage SOYATT - Avril 2026...
echo.
python verif_qp_soyatt.py
echo.
pause
