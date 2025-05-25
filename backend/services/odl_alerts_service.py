import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models.odl import ODL
from models.odl_log import ODLLog
from models.parte import Parte
from models.tool import Tool
from schemas.odl_alerts import ODLAlertRead, ODLAlertsResponse

logger = logging.getLogger(__name__)

class ODLAlertsService:
    """Servizio per la gestione degli alert degli ODL"""
    
    @staticmethod
    def genera_alerts_odl(db: Session) -> ODLAlertsResponse:
        """
        Genera alert per ODL basati su regole di business
        
        Args:
            db: Sessione database
            
        Returns:
            ODLAlertsResponse: Lista degli alert generati
        """
        try:
            alerts = []
            
            # Ottieni tutti gli ODL attivi con informazioni correlate
            odl_query = db.query(
                ODL,
                Parte.nome.label('parte_nome'),
                Tool.nome.label('tool_nome')
            ).join(
                Parte, ODL.parte_id == Parte.id
            ).join(
                Tool, ODL.tool_id == Tool.id
            ).filter(
                ODL.status != 'Finito'
            )
            
            for odl, parte_nome, tool_nome in odl_query.all():
                # Calcola tempo nello stato corrente
                tempo_in_stato = ODLAlertsService._calcola_tempo_in_stato_corrente(db, odl.id, odl.status)
                
                # Alert per ODL in ritardo (più di 24 ore nello stesso stato)
                if tempo_in_stato and tempo_in_stato > 1440:  # 24 ore
                    alerts.append(ODLAlertRead(
                        id=f"ritardo_{odl.id}",
                        odl_id=odl.id,
                        tipo="ritardo",
                        titolo=f"ODL #{odl.id} in ritardo",
                        descrizione=f"L'ODL è nello stato '{odl.status}' da più di 24 ore",
                        timestamp=datetime.now(),
                        parte_nome=parte_nome,
                        tool_nome=tool_nome,
                        tempo_in_stato=tempo_in_stato,
                        azione_suggerita="Verificare lo stato del processo e sbloccare se necessario"
                    ))
                
                # Alert per ODL bloccati in preparazione
                if odl.status == 'Preparazione' and tempo_in_stato and tempo_in_stato > 480:  # 8 ore
                    alerts.append(ODLAlertRead(
                        id=f"blocco_{odl.id}",
                        odl_id=odl.id,
                        tipo="blocco",
                        titolo=f"ODL #{odl.id} bloccato in preparazione",
                        descrizione=f"L'ODL è in preparazione da più di 8 ore",
                        timestamp=datetime.now(),
                        parte_nome=parte_nome,
                        tool_nome=tool_nome,
                        tempo_in_stato=tempo_in_stato,
                        azione_suggerita="Verificare disponibilità tool e risorse"
                    ))
                
                # Alert per ODL ad alta priorità in attesa
                if odl.priorita >= 4 and odl.status == 'Attesa Cura':
                    alerts.append(ODLAlertRead(
                        id=f"priorita_{odl.id}",
                        odl_id=odl.id,
                        tipo="warning",
                        titolo=f"ODL #{odl.id} alta priorità in attesa",
                        descrizione=f"ODL con priorità {odl.priorita} in attesa di cura",
                        timestamp=datetime.now(),
                        parte_nome=parte_nome,
                        tool_nome=tool_nome,
                        azione_suggerita="Considerare prioritizzazione nella schedulazione"
                    ))
                
                # Alert per ODL in cura da troppo tempo
                if odl.status == 'Cura' and tempo_in_stato and tempo_in_stato > 2880:  # 48 ore
                    alerts.append(ODLAlertRead(
                        id=f"cura_lunga_{odl.id}",
                        odl_id=odl.id,
                        tipo="critico",
                        titolo=f"ODL #{odl.id} in cura da troppo tempo",
                        descrizione=f"L'ODL è in cura da più di 48 ore",
                        timestamp=datetime.now(),
                        parte_nome=parte_nome,
                        tool_nome=tool_nome,
                        tempo_in_stato=tempo_in_stato,
                        azione_suggerita="Verificare il ciclo di cura e lo stato dell'autoclave"
                    ))
                
                # Alert per ODL con motivo di blocco
                if odl.motivo_blocco:
                    alerts.append(ODLAlertRead(
                        id=f"motivo_blocco_{odl.id}",
                        odl_id=odl.id,
                        tipo="blocco",
                        titolo=f"ODL #{odl.id} bloccato",
                        descrizione=f"Motivo: {odl.motivo_blocco}",
                        timestamp=datetime.now(),
                        parte_nome=parte_nome,
                        tool_nome=tool_nome,
                        azione_suggerita="Risolvere il motivo del blocco indicato"
                    ))
            
            # Calcola statistiche per tipo
            per_tipo = {}
            for alert in alerts:
                per_tipo[alert.tipo] = per_tipo.get(alert.tipo, 0) + 1
            
            logger.info(f"Generati {len(alerts)} alert per ODL")
            
            return ODLAlertsResponse(
                alerts=alerts,
                totale=len(alerts),
                per_tipo=per_tipo
            )
            
        except Exception as e:
            logger.error(f"Errore durante la generazione degli alert: {str(e)}")
            return ODLAlertsResponse(alerts=[], totale=0, per_tipo={})
    
    @staticmethod
    def _calcola_tempo_in_stato_corrente(db: Session, odl_id: int, stato_corrente: str) -> int:
        """
        Calcola il tempo trascorso nello stato corrente (in minuti)
        
        Args:
            db: Sessione database
            odl_id: ID dell'ODL
            stato_corrente: Stato corrente dell'ODL
            
        Returns:
            int: Minuti trascorsi nello stato corrente
        """
        try:
            # Trova l'ultimo log di ingresso nello stato corrente
            ultimo_log = db.query(ODLLog).filter(
                and_(
                    ODLLog.odl_id == odl_id,
                    ODLLog.stato_nuovo == stato_corrente
                )
            ).order_by(ODLLog.timestamp.desc()).first()
            
            if not ultimo_log:
                # Se non c'è log, usa la data di creazione dell'ODL
                odl = db.query(ODL).filter(ODL.id == odl_id).first()
                if odl:
                    delta = datetime.now() - odl.created_at
                    return int(delta.total_seconds() / 60)
                return 0
            
            # Calcola il tempo dall'ultimo cambio di stato
            delta = datetime.now() - ultimo_log.timestamp
            return int(delta.total_seconds() / 60)
            
        except Exception as e:
            logger.error(f"Errore nel calcolo tempo in stato per ODL {odl_id}: {str(e)}")
            return 0
    
    @staticmethod
    def ottieni_alerts_critici(db: Session) -> List[ODLAlertRead]:
        """
        Ottiene solo gli alert critici e di blocco
        
        Args:
            db: Sessione database
            
        Returns:
            List[ODLAlertRead]: Lista degli alert critici
        """
        all_alerts = ODLAlertsService.genera_alerts_odl(db)
        return [alert for alert in all_alerts.alerts if alert.tipo in ['critico', 'blocco']]
    
    @staticmethod
    def ottieni_statistiche_alerts(db: Session) -> Dict[str, Any]:
        """
        Ottiene statistiche sugli alert
        
        Args:
            db: Sessione database
            
        Returns:
            Dict[str, Any]: Statistiche degli alert
        """
        alerts_response = ODLAlertsService.genera_alerts_odl(db)
        
        return {
            'totale_alerts': alerts_response.totale,
            'per_tipo': alerts_response.per_tipo,
            'alerts_critici': len([a for a in alerts_response.alerts if a.tipo == 'critico']),
            'alerts_blocco': len([a for a in alerts_response.alerts if a.tipo == 'blocco']),
            'alerts_ritardo': len([a for a in alerts_response.alerts if a.tipo == 'ritardo']),
            'alerts_warning': len([a for a in alerts_response.alerts if a.tipo == 'warning']),
            'timestamp_generazione': datetime.now()
        } 