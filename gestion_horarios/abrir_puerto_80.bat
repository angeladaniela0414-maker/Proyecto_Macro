@echo off
REM Ejecutar como Administrador: permite que otros equipos de la red entren al portal.
netsh advfirewall firewall add rule name="Portal ULEAM HTTP 80" dir=in action=allow protocol=TCP localport=80
pause
