import yaml
from typing import List, Dict

class ComplianceChecker:
    def __init__(self, rules_path: str = "rules/review_rules.yaml"):
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
    
    def check_compliance(self, text: str) -> List[str]:
        """合规性检查"""
        results = []
        for check in self.rules['compliance_checks']:
            found = any(keyword in text for keyword in check['keywords'])
            if check['required'] and found:
                results.append(f"{check['name']}完整")
            elif check['required'] and not found:
                results.append(f"缺少{check['name']}")
        return results
    
    def identify_risks(self, text: str) -> List[Dict]:
        """风险识别"""
        risks = []
        for pattern in self.rules['risk_patterns']:
            if any(keyword in text for keyword in pattern['keywords']):
                risks.append({
                    "clause": "待定位",
                    "issue": pattern['name'],
                    "severity": pattern['severity']
                })
        return risks