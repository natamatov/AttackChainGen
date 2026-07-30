# Analyst Guide: Vector 4 - Living off the Land (LotL)

## 1. Overview
Living off the Land (LotL) атаки крайне сложно детектировать, так как злоумышленники не загружают свои хакерские инструменты, а используют штатные системные программы. В данном сценарии на ПК директора (`PC-DIRECTOR`) используется `certutil.exe` для скачивания скрипта. Затем с помощью легитимного WinRM атакующий удаленно подключается к запасному контроллеру домена (`AD03`), где с помощью PowerShell сжимает (архивирует) конфиденциальные файлы для их последующей кражи.

## 2. Detection & Triage

### KQL: Использование certutil для скачивания (LotL)
Ищем запуски `certutil` с ключами `-urlcache`, `-split` и `-f`, которые типичны для скачивания файлов из интернета.
```kql
winlog.event_id: "4688"
  AND process.name: "certutil.exe"
  AND process.command_line: *urlcache*
```

### KQL: Удаленное выполнение через WinRM
Отслеживаем создание PowerShell-сессий и процессов WMI, запущенных через службу `wsmprovhost.exe`.
```kql
winlog.event_id: "4688"
  AND process.parent.name: "wsmprovhost.exe"
  AND process.name: "powershell.exe"
```

### KQL: Подозрительная архивация данных
Мониторинг PowerShell-команд, направленных на сбор и сжатие большого количества файлов.
```kql
winlog.event_id: "4688"
  AND process.name: "powershell.exe"
  AND process.command_line: *Compress-Archive*
```

## 3. Investigation Steps

1. **Анализ PC-DIRECTOR (192.168.100.24):**
   - Выясните происхождение первоначального запуска (был ли это документ Office с макросами или фишинговая ссылка?).
   - Изучите сетевой трафик (или логи Proxy/DNS) к домену `http://malicious-domain.com`.
2. **Анализ AD03 (192.168.100.3):**
   - Найдите файл `C:\Windows\Temp\backup.zip` и проверьте, не был ли он уже отправлен наружу (Event ID 3 для процессов ftp.exe, curl.exe, powershell.exe).
   - Выясните, какие именно файлы попали в архив.

## 4. Containment & Remediation
- Заблокируйте домен C2 на уровне корпоративного DNS / Proxy.
- Ограничьте выполнение PowerShell-скриптов с помощью политики ExecutionPolicy, если это возможно, либо включите Constrained Language Mode.
- Временно запретите WinRM-входы на серверы для обычных пользовательских учетных записей.

---

# Investigation Checklist

- [ ] Вредоносный домен добавлен в блок-листы NGFW/Proxy.
- [ ] Исходный скрипт `script.ps1` извлечен и передан на анализ.
- [ ] Архив `backup.zip` удален с контроллера домена до того, как его успели выгрузить.
- [ ] Ограничен доступ к WinRM для учетной записи `director`.
- [ ] Включено логирование PowerShell Script Block (Event ID 4104) для всех хостов.
