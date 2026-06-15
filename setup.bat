@echo off
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
cd ..

echo.
echo Installing frontend dependencies...
cd frontend
npm install
cd ..

echo.
echo Setup complete! Run start-dev.bat to start.
pause
