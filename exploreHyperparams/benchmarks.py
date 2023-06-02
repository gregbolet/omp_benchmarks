
ROOT_DIR = '/g/g15/bolet1/workspace/ruby-benchmarks'


machines = {
    'ruby' : {
        'OMP_NUM_THREADS': [4,8,14,28,42,56,70,112],
        'OMP_PROC_BIND': ['close', 'spread'],
        'OMP_SCHEDULE_sched': ['static', 'guided', 'dynamic'],
        'OMP_SCHEDULE_chunk': [1,8,32,64,128,256,512]
    },

    'lassen' : {
        'OMP_NUM_THREADS': [10,20,40,60,80,100,120,140,160],
        'OMP_PROC_BIND': ['close', 'spread'],
        'OMP_SCHEDULE_sched': ['static', 'guided', 'dynamic'],
        'OMP_SCHEDULE_chunk': [1,8,32,64,128,256,512]
    }
}


# modified lulesh to do 200 iterations instead of 1000
# will need to change region-execs to match correct number of region executions
progs = {
    'nas_bt': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'medprob': {
            'exe': 'bt.C.x',
        },
        'lrgprob': {
            'exe': 'bt.D.x',
        }
    },
    'lulesh': {
        'xtime-regex': r'(?<=\()\s*(\d*\.\d*)(?= overall\))',
        'smallprob': {
            'exe': 'lulesh2.0 -s 30 -r 100 -b 0 -c 8 -i 200',
        },
        'medprob': {
            'exe': 'lulesh2.0 -s 55 -r 100 -b 0 -c 8 -i 200',
        },
        'lrgprob': {
            'exe': 'lulesh2.0 -s 80 -r 100 -b 0 -c 8 -i 200',
        }
    },
    'nas_ft': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'medprob': {
            'exe': 'ft.C.x',
        },
        'lrgprob': {
            'exe': 'ft.D.x',
        }
    },
    'nas_cg': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'medprob': {
            'exe': 'cg.C.x',
        },
        'lrgprob': {
            'exe': 'cg.D.x',
        }
    }
}
