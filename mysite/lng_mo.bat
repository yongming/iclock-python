cd ../
call init.bat
cd mysite
python manage.py compilemessages
python "%INSTALL_PATH%\django\bin\compile-messages.py"
pause
