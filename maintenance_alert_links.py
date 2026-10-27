"""Read the database-managed relationships between alerts and maintenance jobs."""
from assets import database_integration as db


def schedules_for_alerts(client, alerts):
    """Return each alert's newest non-cancelled linked job, never an engine guess."""
    engine_by_alert = {str(a['id']): str(a['engine_id']) for a in alerts
                       if a.get('id') and a.get('engine_id')}
    if not engine_by_alert:
        return {}
    links = db.fetch_records(client, 'maintenance_alerts',
        'alert_id,maintenance_schedule_id,linked_at',
        filters=[('in_', 'alert_id', list(engine_by_alert))],
        order_by=[('linked_at', True), ('maintenance_schedule_id', True)]).data or []
    ids = list({str(link['maintenance_schedule_id']) for link in links})
    if not ids:
        return {}
    schedules = db.fetch_records(client, 'maintenance_schedules',
        'id,engine_id,scheduled_date,created_by,assign_to,status,started_at,completed_at,start_time,end_time',
        filters=[('in_', 'id', ids)]).data or []
    by_id = {str(s['id']): s for s in schedules}
    result = {}
    for link in links:
        alert_id = str(link['alert_id'])
        job = by_id.get(str(link['maintenance_schedule_id']))
        if (job and alert_id not in result
                and job.get('status') not in ('cancelled', 'canceled')
                and str(job.get('engine_id')) == engine_by_alert.get(alert_id)):
            result[alert_id] = job
    return result
