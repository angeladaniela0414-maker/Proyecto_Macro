@echo off
REM Ejecutar UNA VEZ como Administrador: permite que otros equipos de la red entren.
netsh advfirewall firewall add rule name="Horarios ULEAM HTTP 80" dir=in action=allow protocol=TCP localport=80
pause
