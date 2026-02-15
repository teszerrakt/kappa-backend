def post_fork(server, worker):
    """Start the background precompute thread in each worker after fork.

    With --preload, the app is loaded once in the master process before forking.
    Threads do not survive fork(), so we restart the precompute thread in each
    worker.  The first worker to run will compute and save to SQLite; subsequent
    workers will find the data already in the database and load it instantly.
    """
    from kappa.main import start_precompute_thread

    start_precompute_thread()
    server.log.info("Background precompute thread started in worker %s", worker.pid)
