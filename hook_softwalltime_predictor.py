import pbs
import sys

sys.path.insert(1, "/opt/pbs/lib/softwalltime")
try:
    import softwalltime_psql
except Exception as err:
    pbs.logmsg(pbs.EVENT_ERROR, "softwalltime_predictor hook failed to import softwalltime_psql " % str(err))
    pbs.event().accept()


class Starter(softwalltime_psql.Predictor):
    def __init__(self):
        super().__init__()

    def run(self, job):
        soft_walltime = self.walltime2sec(job.Resource_List["soft_walltime"])

        if soft_walltime:
           
            nodes = job.Resource_List["select"]
            if nodes:
                nodes = str(nodes)
            else:
                nodes = "unknown"

            nodect = job.Resource_List["nodect"]
            if not nodect:
                nodect = 0

            ncpus = job.Resource_List["ncpus"]
            if not ncpus:
                ncpus = 0

            ngpus = job.Resource_List["ngpus"]
            if not ngpus:
                ngpus = 0

            mem = job.Resource_List["mem"]
            if not mem:
                mem = 0
            else:
                mem = self.mem2kb(mem)

            interactive = 'false'
            if (job.interactive):
                interactive = 'true'

            walltime = self.walltime2sec(job.Resource_List["walltime"])

            self.connect()
            self.check_table(self.table_name)
            if soft_walltime and not self.check_job_exists(job.id):
                self.insert_run_job(job.id, job.Job_Owner.split("@")[0], job.Job_Name, job.queue, nodes, nodect, ncpus, ngpus, mem, interactive, soft_walltime, walltime)
            self.disconnect()

class Setter(softwalltime_psql.Predictor):
    def __init__(self):
        super().__init__()

    def run(self, job, owner):

        self.connect()
        self.check_table(self.table_name)
        soft_walltime = self.predicted_avg_walltime(owner)
        self.disconnect()

        if soft_walltime:
            ### 2.11.2021 - 15 minutes added ###
            soft_walltime += 900

            walltime = self.walltime2sec(job.Resource_List["walltime"])
            if walltime == 0:
                walltime = 86400

            if soft_walltime > walltime:
                soft_walltime = walltime
            job.Resource_List["soft_walltime"] = pbs.duration(soft_walltime)
            pbs.logmsg(pbs.EVENT_DEBUG, "softwalltime_predictor hook predicting: %s %s %d" % (job.id, owner, soft_walltime,))

        return



e = pbs.event()
try:
#if True:
    o = None

    if e.type == pbs.QUEUEJOB:
        o = Setter()
        o.run(e.job, e.requestor)

    if e.type == pbs.RUNJOB:
        o = Starter()
        o.run(e.job)

except SystemExit:
    pass
except Exception as err:
    pbs.logmsg(pbs.EVENT_DEBUG, "softwalltime_predictor hook failed: %s" % str(err).replace("\n", ";"))
    e.accept()
