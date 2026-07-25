import subprocess
import logging

logging.basicConfig(
    filename="pipeline_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

scripts = [
    "fetch_jobs.py",
    "clean_data.py",
    "load_to_db.py"
]

logging.info("=== Pipeline run started ===")

pipeline_success = True

for script in scripts:
    print(f"Running {script}...")
    logging.info(f"Running {script}...")
    result = subprocess.run(["python", script])

    if result.returncode != 0:
        print(f"❌ {script} failed. Stopping pipeline.")
        logging.error(f"{script} failed with return code {result.returncode}. Pipeline stopped.")
        pipeline_success = False
        break
    else:
        print(f"✅ {script} completed successfully.")
        logging.info(f"{script} completed successfully.")

if pipeline_success:
    logging.info("=== Pipeline run finished successfully ===")
    print("\n🎉 Pipeline completed successfully.")
else:
    logging.info("=== Pipeline run finished with failure ===")
    print("\n⚠️ Pipeline stopped due to a failure. Check pipeline_log.txt for details.")