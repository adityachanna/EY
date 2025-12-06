
import json
import random
from typing import Dict, List, Any

class MockIQVIA:
    """
    Mock API for IQVIA specific to the request context.
    Returns market size, growth, and competitor data.
    """
    def __init__(self):
        self.market_data = {
            "depression": {
                "market_size_usd_bn": 15.6,
                "cagr_percent": 3.7,
                "market_share": {
                    "SSRIs": "35%",
                    "SNRIs": "25%",
                    "Atypical Antipsychotics": "20%",
                    "Others": "20%"
                },
                "competitors": ["Pfizer (Zoloft)", "Eli Lilly (Prozac)", "AbbVie"]
            },
            "alzheimers": {
                "market_size_usd_bn": 6.8,
                "cagr_percent": 8.5,
                "market_share": {
                    "Cholinesterase inhibitors": "55%",
                    "NMDA receptor antagonists": "30%",
                    "Pipeline (Monoclonal Antibodies)": "15%"
                },
                "competitors": ["Biogen (Aduhelm)", "Eisai", "Novartis"]
            },
            "minocycline": {
                "market_size_usd_bn": 0.45,
                "cagr_percent": -2.1,
                "segment": "Generics (Antibiotics)",
                "major_players": ["Teva", "Sandoz", "Sun Pharma", "Dr. Reddy's"]
            },
            "respiratory": {
                "market_size_usd_bn": 28.5,
                "cagr_percent": 5.2,
                "market_share": {
                    "Inhalers (ICS/LABA)": "60%",
                    "Biologics": "20%",
                    "Oral (Leukotriene Modifiers)": "10%",
                    "Others": "10%"
                },
                "competitors": ["GSK", "AstraZeneca", "Cipla (India)"]
            },
            "telmisartan": {
                "market_size_usd_bn": 3.2,
                "cagr_percent": 1.5,
                "segment": "Cardiovascular (Hypertension)",
                "major_players": ["Boehringer Ingelheim", "Microlabs", "Lupin"]
            },
            "metformin": {
                 "market_size_usd_bn": 0.8,
                 "cagr_percent": 1.0,
                 "segment": "Diabetes (Type 2)",
                 "growth_driver": "Potential anti-aging applications (TAME trial hype)"
            }
        }

    def get_market_insights(self, query: str) -> Dict[str, Any]:
        """
        Simulates querying IQVIA for market data.
        """
        query = query.lower()
        if "depression" in query or "mdd" in query:
            return {"status": "success", "data": self.market_data["depression"]}
        elif "alzheimer" in query or "neuro" in query:
             return {"status": "success", "data": self.market_data["alzheimers"]}
        elif "minocycline" in query:
             return {"status": "success", "data": self.market_data["minocycline"]}
        elif "respiratory" in query or "asthma" in query or "copd" in query:
             return {"status": "success", "data": self.market_data["respiratory"]}
        elif "telmisartan" in query:
             return {"status": "success", "data": self.market_data["telmisartan"]}
        elif "metformin" in query or "diabetes" in query:
             return {"status": "success", "data": self.market_data["metformin"]}
        else:
            return {
                "status": "partial_success", 
                "message": "Exact match not found. Returning general Generic Market data.",
                "data": {"market_size_usd_bn": 400, "growth": "flat"}
            }

class MockEXIM:
    """
    Mock Server for Export/Import trends.
    """
    def get_export_import_data(self, molecule: str) -> Dict[str, Any]:
        """
        Simulates retrieving import/export volume for a specific molecule.
        """
        if "minocycline" in molecule.lower():
            return {
                "molecule": "Minocycline HCl",
                "total_import_volume_kg": 52000,
                "major_exporters": [
                    {"country": "India", "share": "65%", "top_suppliers": ["Aurobindo", "Sun Pharma"]},
                    {"country": "China", "share": "25%", "top_suppliers": ["Zhejiang Medicine"]},
                    {"country": "Others", "share": "10%"}
                ],
                "price_trend": "Stable",
                "average_price_per_kg_usd": 180
            }
        
        if "telmisartan" in molecule.lower():
             return {
                "molecule": "Telmisartan",
                "total_import_volume_kg": 120000,
                "major_exporters": [
                    {"country": "China", "share": "45%", "top_suppliers": ["Zhejiang Huahai", "Tianyu"]},
                    {"country": "India", "share": "50%", "top_suppliers": ["Hetero", "Aurobindo", "Jubilant"]},
                ],
                "price_trend": "Decreasing",
                "average_price_per_kg_usd": 85
            }

        if "salbutamol" in molecule.lower() or "albuterol" in molecule.lower():
             return {
                "molecule": "Salbutamol Sulphate",
                "total_import_volume_kg": 250000,
                "major_exporters": [
                    {"country": "India", "share": "70%", "top_suppliers": ["Cipla", "Lupin"]},
                    {"country": "China", "share": "20%"}
                ],
                "price_trend": "Volatile",
                "average_price_per_kg_usd": 220
            }
        
        return {"error": "Data not available for this molecule in mock DB."}

class MockUSPTO:
    """
    Mock API for USPTO patent filings.
    """
    def search_patents(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Simulates searching for patents.
        """
        results = []
        keyword = keyword.lower()
        
        if "minocycline" in keyword:
            # Expired composition of matter patent
            results.append({
                "patent_id": "US3148212A",
                "title": "Tetracycline antibiotics (Minocycline)",
                "assignee": "Lederle Labs (Pfizer)",
                "status": "EXPIRED",
                "expiry_date": "1994-02-15",
                "type": "Composition of Matter"
            })
            
            # Repurposing patents (Mock)
            if "depression" in keyword or "neuro" in keyword:
                results.append({
                    "patent_id": "US2018029911A1",
                    "title": "Use of Minocycline for treatment of Treatment-Resistant Depression",
                    "assignee": "University of Japan (Mock)",
                    "status": "PENDING",
                    "filing_date": "2021-06-10",
                    "claim_scope": "Method of use for adjunct therapy"
                })
        
        if "telmisartan" in keyword:
             # Formulation patents
             results.append({
                "patent_id": "US6358986B1",
                "title": "Telmisartan Formulations",
                "assignee": "Boehringer Ingelheim",
                "status": "EXPIRED",
                "expiry_date": "2014-01-01",
                "type": "Formulation"
            })
             if "fibrosis" in keyword or "nash" in keyword:
                 results.append({
                     "patent_id": "WO2020123456",
                     "title": "Use of Telmisartan for treating Liver Fibrosis/NASH",
                     "assignee": "GenFit (Mock)",
                     "status": "PENDING",
                     "filing_date": "2020-05-15"
                 })
                 
        if "inhaler" in keyword and "respiratory" in keyword:
             results.append({
                 "patent_id": "US9876543B2",
                 "title": "Smart Inhaler Device Mechanism",
                 "assignee": "Teva",
                 "status": "ACTIVE",
                 "expiry_date": "2030-05-20"
             })
        
        if not results:
             results.append({"message": "No specific patents found for this query in mock DB."})
             
        return results

class MockClinicalTrials:
    """
    Mock API for ClinicalTrials.gov
    """
    def get_trials(self, search_term: str) -> List[Dict[str, Any]]:
        search_term = search_term.lower()
        trials = []
        
        if "minocycline" in search_term:
            if "depression" in search_term:
                trials.append({
                    "nct_id": "NCT04512345",
                    "title": "Efficacy of Minocycline as Adjunct Therapy in Major Depressive Disorder",
                    "phase": "Phase 2",
                    "status": "Recruiting",
                    "sponsor": "Institute of Psychiatry (Mock)",
                    "locations": ["USA", "UK"],
                    "completion_date": "2025-12"
                })
            elif "alzheimer" in search_term:
                 trials.append({
                    "nct_id": "NCT03356789",
                    "title": "Minocycline in Early Alzheimer's Disease",
                    "phase": "Phase 2",
                    "status": "Completed",
                    "outcome": "Mixed results - reduction in inflammation markers observed",
                    "sponsor": "National Institute on Aging (Mock)"
                })
            else:
                 trials.append({
                    "nct_id": "NCT00001111",
                    "title": "Minocycline for Acne Vulgaris",
                    "phase": "Phase 4",
                    "status": "Completed",
                })
        
        if "telmisartan" in search_term:
             if "fibrosis" in search_term:
                  trials.append({
                    "nct_id": "NCT05566778",
                    "title": "Telmisartan in Idiopathic Pulmonary Fibrosis (IPF)",
                    "phase": "Phase 2",
                    "status": "Recruiting",
                    "sponsor": "University of Alabama (Mock)"
                })
        
        if "metformin" in search_term and "aging" in search_term:
             trials.append({
                 "nct_id": "NCT02432287",
                 "title": "Targeting Aging with Metformin (TAME)",
                 "phase": "Phase 4",
                 "status": "Not yet recruiting",
                 "sponsor": "AFAR (Mock)"
             })
                
        return trials
