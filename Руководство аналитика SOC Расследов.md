Руководство аналитика SOC: Расследование атаки "Phishing to Domain Controller Lateral Movement"

1. Обзор сценария (Executive Summary)

Данный сценарий моделирует многоэтапную кибератаку на инфраструктуру домена corp.local.uz. В качестве точки входа (Initial Access) используется целевой фишинг с применением вредоносного документа Excel, направленный на сотрудника бухгалтерии (PC-Accountant).

После успешной компрометации рабочей станции атакующий выполняет выгрузку пейлоада, проводит внутреннюю сетевую разведку в Active Directory, осуществляет попытку брутфорса учетных записей на файловом сервере (FS01) и совершает боковое перемещение (Lateral Movement) на контроллер домена (AD02), где закрепляется через создание удаленной службы Windows с правами SYSTEM.

2. Карта атаки по MITRE ATT&CK

Этап (Tactic)

Техника (Technique)

ID MITRE

Хост-источник

Хост-цель

Шаблон события

Initial Access

Phishing: Spearphishing Attachment

T1566.001

PC-Accountant

PC-Accountant

win_sysmon_1_process_creation

Execution / Persistence

Ingress Tool Transfer

T1105

PC-Accountant

PC-Accountant

sysmon_event_11

Discovery

Account Discovery: Domain Account

T1087.002

PC-Accountant

AD02

sysmon_event_3

Credential Access

Brute Force: Password Guessing

T1110.001

PC-Accountant

FS01

win_security_4625

Lateral Movement

Remote Services: SMB/Windows Admin Shares

T1021.002

PC-Accountant

AD02

win_security_4624

Execution / Persistence

Create or Modify System Process: Windows Service

T1543.003

AD02

AD02

win_security_4688

3. KQL-запросы для Elastic Security / Kibana

Шаг 1: Поиск запуска подозрительных дочерних процессов из офисных приложений (Initial Access)

event.code: "1" and host.hostname: "PC-Accountant" and process.parent.name: ("EXCEL.EXE" or "WINWORD.EXE") and process.name: ("cmd.exe" or "powershell.exe")


Обоснование: Офисные приложения в штатном режиме крайне редко инициируют запуск командного интерпретатора или PowerShell. Любое срабатывание данного правила требует немедленного триажа.

Шаг 2: Поиск создания исполняемых файлов в директориях временных файлов (Payload Dropping)

event.code: "11" and host.hostname: "PC-Accountant" and file.path: "*\\AppData\\Local\\Temp\\*.exe" and process.name: "powershell.exe"


Обоснование: Загрузка исполнимых файлов интерпретатором powershell.exe во временные каталоги пользователя — классический паттерн работы загрузчиков (Dropper/Stager).

Шаг 3: Поиск сетевой активности к контроллерам домена по протоколу LDAP от нестандартных процессов (Recon)

event.code: "3" and host.hostname: "PC-Accountant" and destination.ip: "192.168.100.2" and destination.port: 389 and not process.name: ("lsass.exe" or "svchost.exe" or "SYSTEM")


Обоснование: Несистемные процессы (net_updater.exe), обращающиеся к LDAP (порт 389) контроллера домена, с высокой долей вероятности выполняют автоматизированный сбор информации об объектах AD (BloodHound, AdFind и т.д.).

Шаг 4: Выявление аномальной серии ошибок авторизации SMB (Brute Force / Password Spraying)

event.code: "4625" and destination.ip: "192.168.100.1" and source.ip: "192.168.100.23" and winlog.event_data.LogonType: "3"


Обоснование: Множественные события 4625 с кодом неудачи 0xC000006D (Неверный логин/пароль) с одной рабочей станции на файловый сервер указывают на попытку сетевого подбора паролей.

Шаг 5: Поиск сетевого входа администратора на контроллер домена (Lateral Movement)

event.code: "4624" and host.hostname: "AD02" and winlog.event_data.LogonType: "3" and source.ip: "192.168.100.23" and not winlog.event_data.TargetUserName: ("ANONYMOUS LOGON" or "$*")


Обоснование: Вход с обычной пользовательской рабочей станции (PC-Accountant) на контроллер домена (AD02) по сетевому профилю (Logon Type 3) является отклонением от базовой линии безопасности.

Шаг 6: Обнаружение выполнения команд через удаленное управление службами (Service Execution)

event.code: "4688" and host.hostname: "AD02" and process.parent.name: "services.exe" and process.name: ("cmd.exe" or "powershell.exe") and user.name: "SYSTEM"


Обоснование: Запуск командных оболочек дочерним процессом от services.exe с правами SYSTEM на контроллере домена свидетельствует об успешном исполнении удаленной службы (например, через PsExec, Impacket-psexec или CrackMapExec).

4. План реагирования и расследования (Triage, Analysis, Containment)

4.1 Первичный триаж (Triage)

Валидация инцидента: Проверить цепочку событий на хосте PC-Accountant (192.168.100.23). Подтвердить, что процесс EXCEL.EXE действительно породил cmd.exe с сетевой активностью.

Сбор индикаторов компрометации (IoC):

URL загрузки: http://192.168.100.5/payload.ps1 (Внимание: адрес принадлежит внутреннему почтовому серверу mail01 — возможно, сервер также скомпрометирован или используется для хостинга файлов внутри периметра).

Файловый артефакт: C:\Users\a.karimova\AppData\Local\Temp\net_updater.exe.

Имя сервиса/закладки на DC: dc_backdoor.exe.

4.2 Глубокий анализ (Analysis)

Форензика конечной точки (PC-Accountant):

Изъять дамп оперативной памяти PC-Accountant для анализа инжектированного кода.

Получить копию файла net_updater.exe и отправить в песочницу (Sandbox) / реверс-инжиниринг.

Проверить историю браузера и почтовый клиент учетной записи a.karimova для выявления первоначального фишингового письма.

Анализ контроллера домена (AD02):

Проверить системный реестр на предмет вновь созданных служб: HKLM\SYSTEM\CurrentControlSet\Services\.

Проверить журнал событий Security (Event ID 4697 — создание службы в системе) и System (Event ID 7045).

Оценить объем скомпрометированных учетных записей (была ли скомпрометирована только a.karimova или получены привилегии Enterprise/Domain Admin).

Анализ сетевого трафика (NGFW / Zeek / Suricata):

Проверить логи межсетевых экранов FORTIGATE1 и FORTIGATE2 на наличие аномальных соединений между сегментами PC и Серверы.

4.3 Сдерживание и локализация (Containment & Eradication)

Изоляция хостов:

Немедленно изолировать рабочую станцию PC-Accountant (192.168.100.23) от сети на уровне коммутатора sw1/sw2 или через EDR.

Приостановить сетевое взаимодействие с сервером mail01 (192.168.100.5) для проверки на наличие несанкционированного веб-сервера.

Блокировка учетных записей:

Отключить доменную учетную запись a.karimova.

Инициировать процедуру принудительного сброса паролей для учетных записей, подвергшихся брутфорсу на FS01.

Если на AD02 подтверждены права SYSTEM у атакующего — инициировать процедуру реагирования на полную компрометацию домена (KRBTGT reset, проверка Golden/Silver тикетов).

Удаление артефактов:

Удалить вредоносные службы на AD02 и исполняемые файлы dc_backdoor.exe, net_updater.exe.

5. Чек-лист расследования инцидента (SOC Checklist)

[ ] Шаг 1: Получено и зафиксировано оповещение о подозрительном дочернем процессе EXCEL.EXE на узле PC-Accountant.

[ ] Шаг 2: Проведен анализ скрипта payload.ps1 и сетевой активности узла 192.168.100.23.

[ ] Шаг 3: Проверен почтовый сервер mail01 (192.168.100.5) на предмет размещения вредоносных статических файлов.

[ ] Шаг 4: Извлечен и проанализирован хеш (SHA256) файла net_updater.exe, добавлены блокировки в EDR/NGFW.

[ ] Шаг 5: Проанализированы логи LDAP-запросов на контроллерах домена (AD02, AD03) для оценки ущерба от разведки (Recon).

[ ] Шаг 6: Проверен файловый сервер FS01 (192.168.100.1) на предмет успешных авторизаций после серии ошибок 4625.

[ ] Шаг 7: Хост PC-Accountant изолирован от корпоративной сети.

[ ] Шаг 8: Учетная запись a.karimova заблокирована, пароль сброшен.

[ ] Шаг 9: Проведена верификация целостности контроллера домена AD02 (192.168.100.2), удалена вредоносная служба и исполняемый файл dc_backdoor.exe.

[ ] Шаг 10: Настроено дополнительное правило детектирования в Elastic Security для мониторинга аномальных RPC/SMB соединений к контроллерам домена из пользовательского сегмента.