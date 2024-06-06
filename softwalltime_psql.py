import sys

sys.path.insert(0, "/usr/lib64/python3.6/site-packages")
sys.path.insert(1, "/usr/lib/python3/dist-packages")

try:
    import psycopg2
except Exception as err:
    raise Exception("softwalltime failed to import psycopg2: %s" % str(err))
from configparser import ConfigParser


def config(filename="/opt/pbs/etc/softwalltime.conf",
           section=""):

    parser = ConfigParser()
    parser.read(filename)

    c = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            c[param[0]] = param[1]
    else:
        raise Exception("Section {0} not found in the {1} file"
                        .format(section, filename))

    return c

class Predictor(object):
    def __init__(self):
        self.past_runtimes = []
        self.config = None
        self.conn = None
        self.connected = False
        self.table_name = "softwalltime"

        self.params = config(section="general")
        if not "avg_base_count" in self.params.keys():
            self.params["avg_base_count"] = 2
        if not "perc_base_count" in self.params.keys():
            self.params["perc_base_count"] = 15
        if not "enable_history_cleaning" in self.params.keys():
            self.params["enable_history_cleaning"] = False
        if not "history_size" in self.params.keys():
            self.params["history_size"] = 100

        self.psql_params = config(section="postgresql")
        if not "host" in self.psql_params.keys():
            self.psql_params["host"] = "localhost"
        if not "port" in self.psql_params.keys():
            self.psql_params["port"] = 5455
        if not "database" in self.psql_params.keys():
            self.psql_params["database"] = "walltime_extender"
        if not "user" in self.psql_params.keys():
            self.psql_params["user"] = "postgres"

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.psql_params)
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to connect to database: " + str(err))

        self.connected = True

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
        self.connected = False

    def is_connected(self):
        return self.connected

    def check_table(self, table_name):
        if not self.is_connected():
            return False

        sql = "CREATE TABLE IF NOT EXISTS %s (\
jobid varchar(512), \
owner varchar(256), \
job_name varchar(256), \
queue varchar(256), \
nodes varchar(1024), \
nodect integer,\
ncpus integer,\
ngpus integer,\
mem integer,\
interactive boolean,\
runtime integer, \
soft_walltime integer, \
walltime integer, \
finished boolean,\
date timestamp);" % table_name

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            self.conn.commit()
        except:
            raise Exception("softwalltime_predictor hook failed to check or create table.")

        sql = "CREATE INDEX IF NOT EXISTS softwalltime_lfin ON %s ( owner, finished, date DESC);" % table_name

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            self.conn.commit()
        except:
            raise Exception("softwalltime_predictor hook failed to check or create index.")

        return True

    def check_job_exists(self, jobid):

        res = None

        if not self.is_connected():
            return res

        sql = "SELECT jobid FROM %s WHERE jobid = '%s';" % (self.table_name, jobid)

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            res = cur.fetchone()
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to check jobid: " + str(err))

        return res

    def insert_finished_job_full(self, update, jobid, owner, job_name, queue,  nodes, nodect, ncpus, ngpus, mem, interactive, soft_walltime, walltime, runtime):
        if not self.is_connected():
            return

        if soft_walltime == 0:
            soft_walltime = "NULL"

        if update:
            sql = "UPDATE %s SET queue = '%s', nodes = '%s', nodect = %d, ncpus = %d, ngpus = %d, mem = %d, runtime = %d, soft_walltime = %s, walltime = %d, finished = true, date = NOW() WHERE jobid = '%s'" \
% (self.table_name, queue, nodes, nodect, ncpus, ngpus, mem, runtime, soft_walltime, walltime, jobid)
        else:
            sql = "INSERT INTO %s (jobid, owner, job_name, queue, nodes, nodect, ncpus, ngpus, mem, runtime, soft_walltime, walltime, finished, date) \
VALUES ('%s', '%s', '%s', '%s', '%s', %d, %d, %d, %d, %d, %s, %d, true, NOW());" \
% (self.table_name, jobid, owner, job_name, queue, nodes, nodect, ncpus, ngpus, mem, runtime, soft_walltime, walltime)

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to insert finished job (full) into database: " + str(err))

    def insert_finished_job(self, update, jobid, owner, runtime, walltime):
        if not self.is_connected():
            return

        if update:
            sql = "UPDATE %s SET runtime = %d, walltime = %d, finished = true, date = NOW() WHERE jobid = '%s'" \
% (self.table_name, runtime, walltime, jobid)
        else:
            sql = "INSERT INTO %s (jobid, owner, runtime, walltime, finished, date) \
VALUES ('%s', '%s', %d, %d, true, NOW());" \
% (self.table_name, jobid, owner, runtime, walltime)

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to insert finished job into database: " + str(err))

    def insert_run_job(self, jobid, owner, job_name, queue,  nodes, nodect, ncpus, ngpus, mem, interactive, soft_walltime, walltime):

        if not self.is_connected():
            return

        sql = "INSERT INTO %s (jobid, owner, job_name, queue, nodes, nodect, ncpus, ngpus, mem, interactive, soft_walltime, walltime, finished, date) \
VALUES ('%s', '%s', '%s', '%s', '%s', %d, %d, %d, %d, '%s', %d, %d, false, NOW());" \
% (self.table_name, jobid, owner, job_name, queue, nodes, nodect, ncpus, ngpus, mem, interactive, soft_walltime, walltime)

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to insert queued job into database: " + str(err))

    def clean_old_records(self):

        if not bool(self.params["enable_history_cleaning"]):
            return

        if not self.is_connected():
            return

        sql = " \
do $$ \
declare \
	i record; \
begin \
    for i in \
        select distinct owner from %s \
    loop \
        DELETE FROM %s WHERE owner = i.owner AND jobid NOT IN (SELECT jobid FROM %s WHERE owner = i.owner ORDER BY date DESC LIMIT %d); \
    end loop; \
end; $$ \
; " % (self.table_name, self.table_name, self.table_name, int(self.params["history_size"]))

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor failed to clean old records: " + str(err))

    def predicted_avg_walltime(self, owner):
        res = 0
        if not self.is_connected():
            return res

        count = int(self.params["avg_base_count"])

        sql = "SELECT AVG(runtime) FROM (SELECT runtime FROM %s WHERE owner = '%s' AND finished = true ORDER BY date DESC LIMIT %d) AS runtimes;" % (self.table_name, owner, count)

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            res = cur.fetchone()[0]
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to predict walltime: " + str(err))

        return res

    def predicted_perc_coefficient(self, owner):
        res = 0
        if not self.is_connected():
            return res

        count = int(self.params["perc_base_count"])

        sql = "SELECT MAX(perc) FROM (SELECT ((runtime * 1.0)/ (walltime * 1.0)) AS perc FROM %s WHERE owner = '%s' AND finished = true ORDER BY date DESC LIMIT %d) AS percentages;" % (self.table_name, owner, count)

        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            res = cur.fetchone()[0]
            cur.close()
            self.conn.commit()
        except Exception as err:
            raise Exception("softwalltime_predictor hook failed to predict perc_coefficient: " + str(err))

        return res

    def walltime2sec(self, w):
        s = str(w).split(":")
        if len(s) == 1:
            seconds = int(s[0])
        elif len(s) == 2:
            seconds = int(s[0]) * 60
            seconds += int(s[1])
        elif len(s) == 3:
            seconds = int(s[0]) * 60 * 60
            seconds += int(s[1]) * 60
            seconds += int(s[2])
        else:
            return 0
        return seconds

    def mem2kb(self, mem):
        res = 0

        try:
            mem = str(mem).lower()

            if mem.endswith("kb"):
                res = mem.replace("kb", "")
                res = int(res)

            if mem.endswith("mb"):
                res = mem.replace("mb", "")
                res = int(res) * 1024

            if mem.endswith("gb"):
                res = mem.replace("gb", "")
                res = int(res) * 1024 * 1024
        
            if mem.endswith("tb"):
                res = mem.replace("tb", "")
                res = int(res) * 1024 * 1024 * 1024
        except:
            return 0

        return res
