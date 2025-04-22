from apscheduler.schedulers.background import BackgroundScheduler
from app.services.cpu import get_cpu_data
from app.services.machines import get_all_machines
from app.views.cpu import save_cpu_data
from app import db

def start_scheduler(app):
    scheduler = BackgroundScheduler()

    def collect_cpu_data():
        with app.app_context():  # Aqui estamos forçando o contexto da aplicação
            machine_names_full = get_all_machines()
            machine_names = [entry["name"].split(".")[0] for entry in machine_names_full]
            for machine_name in machine_names:
                try:
                    data = get_cpu_data(machine_name)
                    # save_cpu_data(machine_name, data)
                except Exception as e:
                    continue
                    # print(f"[Scheduler] Erro ao coletar CPU: {e}")

    scheduler.add_job(collect_cpu_data, 'interval', seconds=60)
    scheduler.start()