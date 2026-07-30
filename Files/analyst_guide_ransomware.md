# Руководство аналитика: Double Extortion Ransomware

## 1. Обнаружение (Detection)
Ransomware обычно проявляется двумя паттернами: кража данных и последующее шифрование с удалением бэкапов.

**KQL для поиска аномальной выгрузки (Exfiltration):**
```kql
event.code: "4688" AND process.command_line: *rclone*
```
```kql
event.code: "3" AND process.name: "rclone.exe"
```

**KQL для поиска удаления теневых копий:**
```kql
event.code: "4688" AND process.name: "vssadmin.exe" AND process.command_line: *delete* AND process.command_line: *shadows*
```

**KQL для массового создания зашифрованных файлов:**
```kql
event.code: "11" AND file.name: *.enc
```

---

# Чеклист расследования

## Артефакты
- [ ] IP-адрес назначения выгрузки (Exfiltration IP)
- [ ] Скомпрометированный пользователь (User)
- [ ] Имя вредоносного процесса-шифровальщика

## Действия
- [ ] Изолировать скомпрометированный хост от сети (PC-Accountant).
- [ ] Заблокировать IP злоумышленника (192.168.100.253) на NGFW.
- [ ] Оценить объем утекших данных (по размеру трафика на Sysmon Event 3 или логам NGFW).
- [ ] Инициировать процедуру восстановления из офлайн-бэкапов.
