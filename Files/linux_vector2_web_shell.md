# Analyst Guide: Linux Vector 2 - Web-to-Shell & Cryptominer

## 1. Overview
В данном сценарии веб-приложение, запущенное на почтовом сервере `mail01`, было скомпрометировано (RCE). Легитимный процесс веб-сервера (`nginx` / `apache2`) породил bash-оболочку и открыл Reverse Shell к атакующему. Затем злоумышленник повысил права до `root` с помощью уязвимой конфигурации `sudo` (awk GTFOBins) и установил скрытый криптомайнер XMRig в системную директорию `/tmp/.X11-unix/`.

## 2. Detection & Triage

### KQL: Веб-сервер порождает командную оболочку
Ищем события auditd/sysmon, где родительским процессом является веб-сервер, а дочерним - интерактивный shell.
```kql
event.dataset: "auditd.log"
  AND process.parent.name: ("nginx" OR "apache2" OR "httpd")
  AND process.name: ("bash" OR "sh" OR "dash")
```

### KQL: Подозрительное использование Sudo (GTFOBins)
Ищем выполнение команд с sudo, которые часто используются для повышения привилегий через встроенные бинарники.
```kql
event.dataset: "auditd.log"
  AND process.name: "sudo"
  AND process.command_line: (*awk* OR *vi* OR *find* OR *less*)
```

### KQL: Создание скрытых исполняемых файлов в /tmp
Мониторинг создания бинарных файлов в скрытых директориях временных папок.
```kql
winlog.channel: "Linux-Sysmon/Operational"
  AND winlog.event_id: "11"
  AND file.path: /tmp/.*/xmrig*
```

## 3. Investigation Steps

1. **Анализ логов веб-сервера (192.168.100.5):**
   - Просмотрите `/var/log/nginx/access.log` (или error.log), чтобы найти аномальные HTTP-запросы (POST-запросы с подозрительными payload) перед запуском Reverse Shell.
2. **Анализ криптомайнера:**
   - Извлеките файл `/tmp/.X11-unix/xmrig` и его конфигурационный файл (`config.json`), чтобы узнать IP пула и кошелек злоумышленника.
   - Проверьте наличие cron-задач (`crontab -l -u root` и файлы в `/etc/cron.*`), так как майнеры всегда прописываются в автозагрузку.

## 4. Containment & Remediation
- Заблокируйте IP-адрес злоумышленника (203.0.113.88) и IP-адреса майнинг-пулов.
- Завершите процессы майнера (`kill -9 PID`) и Reverse Shell.
- Исправьте конфигурацию `/etc/sudoers`, запретив веб-пользователю `www-data` использовать `sudo`.
- Установите WAF (Web Application Firewall) для защиты от RCE-уязвимостей.

---

# Investigation Checklist

- [ ] Вектор первоначального проникновения через веб-уязвимость идентифицирован.
- [ ] Оболочка Reverse Shell терминирована.
- [ ] IP C2 сервера заблокирован на NGFW.
- [ ] Бинарный файл майнера и его скрипты автозагрузки (`cron`/`systemd`) удалены.
- [ ] Проведена ревизия прав в файле `/etc/sudoers`.
