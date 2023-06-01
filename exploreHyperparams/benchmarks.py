ROOT_DIR = '/g/g15/bolet1/workspace/lassen-benchmarks'

machines = {
    'ruby' : {
        'envvars': {
            'OMP_NUM_THREADS': [str(a) for a in [4,8,14,28,42,56,70,112]],
            'OMP_PROC_BIND': ['close', 'spread'],
            'OMP_SCHEDULE': [ a+','+str(b) for a in ['static', 'guided', 'dynamic'] for b in [1,8,32,64,128,256,512] ],
        },
        'jobsystem' : {
            'joblaunch' : 'sbatch jobfileSbatch.sh'
        }
    },

    'lassen' : {
        'envvars': {
            'OMP_NUM_THREADS': [str(a) for a in [10,20,40,60,80,100,120,140,160]],
            'OMP_PROC_BIND': ['close', 'spread'],
            'OMP_SCHEDULE': [ a+','+str(b) for a in ['static', 'guided', 'dynamic'] for b in [1,8,32,64,128,256,512] ],
        },
        'jobsystem' : {
            'joblaunch' : 'bsub jobfileBsub.sh'
        }
    }
}

progs = {
    'bt_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'exe': {
            'smlprob': './bt.B.x',
            'medprob': './bt.C.x',
            'lrgprob': './bt.D.x'
        }
    },
    'cg_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'exe': {
            'smlprob': './cg.B.x',
            'medprob': './cg.C.x',
            'lrgprob': './cg.D.x'
        }
    },
    'ft_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'exe': {
            'smlprob': './ft.B.x',
            'medprob': './ft.C.x',
            'lrgprob': './ft.D.x'
        }
    },
    'lu_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'exe': {
            'smlprob': './lu.B.x',
            'medprob': './lu.C.x',
            'lrgprob': './lu.D.x'
        }
    },
    'bfs_rodinia': {
        'xtime-regex':r'(?<=Compute time: )(\s*\d*\.\d*)(?=\s)',
        'valid-regex':'',
        'exe': {
            'smlprob': './bfs 1 ../inputs/graph4096.txt',
            'medprob': './bfs 1 ../inputs/graph65536.txt',
            'lrgprob': './bfs 1 ../inputs/graph1MW_6.txt'
        }
    },
    'cfd_rodinia': {
        'xtime-regex':r'(?<=Compute time: )(\s*\d*\.\d*)(?=\s)',
        'valid-regex':'',
        'exe': {
            'smlprob': './euler3d_cpu ../inputs/fvcorr.domn.097K',
            'medprob': './euler3d_cpu ../inputs/missile.domn.0.2M',
            'lrgprob': './euler3d_cpu ../inputs/missile.domn.0.4M'
        }
    },
    'hpcg': {
        'xtime-regex':r'(?<=Benchmark Time Summary::Total=)(\d*\.\d*)(?=\s)',
        'valid-regex':r'(?<=Final Summary::)(Results are valid)(?=\s)',
        'exe': {
            'smlprob': 'rm *.txt && ./xhpcg --nx=32 --ny=32 --nz=32 && cat *.txt',
            'medprob': 'rm *.txt && ./xhpcg --nx=128 --ny=128 --nz=128 && cat *.txt',
            'lrgprob': 'rm *.txt && ./xhpcg --nx=200 --ny=200 --nz=200 && cat *.txt'
        }
    },
    'lulesh': {
        'xtime-regex':r'(?<=\()\s*(\d*\.\d*)(?= overall\))',
        'valid-regex':'',
        'exe':{
            'smlprob': './lulesh2.0 -s 30 -r 100 -b 0 -c 8 -i 200',
            'medprob': './lulesh2.0 -s 55 -r 100 -b 0 -c 8 -i 200',
            'lrgprob': './lulesh2.0 -s 80 -r 100 -b 0 -c 8 -i 200',
        }
    },
}