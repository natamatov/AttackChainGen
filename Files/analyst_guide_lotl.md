# Руководство аналитика: Living off the Land (LotL)

## 1. Обнаружение (Detection)
Атаки LotL (использование встроенных утилит Windows) сложно обнаружить, так как используются легитимные файлы, подписанные Microsoft.

**KQL для обнаружения скачивания файлов через certutil:**
```kql
event.code: "4688" AND process.name: "certutil.exe" AND process.command_line: (*urlcache* OR *split*)
```

**KQL для обнаружения подозрительного запуска regsvr32 (Squiblydoo attack):**
```kql
event.code: "4688" AND process.name: "regsvr32.exe" AND process.command_line: (*scrobj.dll* OR */i:*)
```

**KQL для обнаружения создания закрепления через schtasks:**
```kql
event.code: "4688" AND process.name: "schtasks.exe" AND process.command_line: */create*
```

---

# Чеклист расследования

## Артефакты
- [ ] URL пейлоада, скачанного через certutil (http://192.168.100.254/payload.dll).
- [ ] Имя вредоносной DLL на диске (payload.dll).
- [ ] Название запланированной задачи (SystemUpdater).

## Действия
- [ ] Удалить скачанный payload.dll с хоста SERVER-1C.
- [ ] Удалить задачу SystemUpdater из планировщика задач.
- [ ] Проверить сетевые логи на предмет успешных соединений с 192.168.100.254.
