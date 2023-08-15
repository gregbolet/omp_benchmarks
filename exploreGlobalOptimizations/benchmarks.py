import platform, sys, os

# figure out the root directory
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
#ROOT_DIR = ROOT_DIR.replace('/usr/WS2/bolet1', '/g/g15/bolet1/workspace')
print('ROOT_DIR', ROOT_DIR)

# figure out what machine we're on, we only assume single node runs
MACHINE=None
uname = str(platform.uname().node)
if 'lassen' in uname:
    MACHINE = 'lassen'
    os.sched_setaffinity(0, list(range(8,88))+list(range(96,176)))
elif 'ruby' in uname:
    MACHINE = 'ruby'
    os.sched_setaffinity(0, {i for i in range(112)})
else:
    sys.exit('Unrecognized Machine Type from uname')

# we're going to use the environment vars to control the num threads,
# proc binds, and places while the Apollo instrumentation controls the
# schedule for each of the regions
if MACHINE == 'lassen':
  #num_threads = [160, 80, 40, 20]
  #places = ['threads', 'cores', 'sockets']
  #proc_bind = [ 'close', 'spread' ]

  #num_threads_policies = len(num_threads)
  #num_places_policies = len(places)
  #num_bind_policies = len(proc_bind)

  num_threads_policies = 9
  num_places_policies = 3
  num_bind_policies = 2
  num_region_policies = 22

elif MACHINE == 'ruby':
  #num_threads = [160, 80, 40, 20]
  #places = ['threads', 'cores', 'sockets']
  #proc_bind = [ 'close', 'spread' ]

  num_threads_policies = 10
  num_places_policies = 3
  num_bind_policies = 2
  num_region_policies = 22

  #num_threads_policies = len(num_threads)
  #num_places_policies = len(places)
  #num_bind_policies = len(proc_bind)

  ## this should match the NUM_POLICIES preprocessor define from apollo.h
  #num_region_policies = 15

# specify the job launching approach for each machine
# the timeouts are in units of seconds
machines = {
    'ruby' : {
        #'envvars': {
        #    'OMP_NUM_THREADS': [str(a) for a in [4,8,14,28,42,56,70,84,98,112]],
        #    'OMP_PROC_BIND': ['close', 'spread'],
        #    'OMP_PLACES': ['threads', 'cores', 'sockets'],
        #    'OMP_SCHEDULE': ['static']+[ a+','+str(b) for a in ['static', 'guided', 'dynamic'] for b in [1,4,8,32,64,128,256,512] ],
        #},
        'pythonToModLoad' : 'python/3.10.8',
        'jobsystem' : {
            'runner' : 'sbatch --nodes=1 ',
            'debug' : '--partition=pdebug ', 
            'nodetime' : '--time=', # in format of: minutes
            'output' : '--output=' # can do "path/to/file.log"
        }
    },

    'lassen' : {
        #'envvars': {
        #    'OMP_NUM_THREADS': [str(a) for a in [10,20,40,60,80,100,120,140,160]],
        #    'OMP_PROC_BIND': ['close', 'spread'],
        #    'OMP_PLACES': ['threads', 'cores', 'sockets'],
        #    'OMP_SCHEDULE': ['static']+[ a+','+str(b) for a in ['static', 'guided', 'dynamic'] for b in [1,4,8,32,64,128,256,512] ],
        #},
        'pythonToModLoad' : 'python/3.8.2',
        'jobsystem' : {
            'runner' : 'bsub -nnodes 1 ',
            'debug' : '-qpdebug ', 
            'nodetime' : '-W ', # in format of: minutes
            'output' : '-o ' # can do "path/to/file.log"
        }
    }
}

# specify each program and how to gather/check it's output
progs = {
    'bt_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'dirname' : 'bt',
        'exe': {
            'smlprob': './bt.B.x',
            'medprob': './bt.C.x',
            'lrgprob': './bt.D.x'
        },
        'timeout':{
            'smlprob': 100,
            'medprob': 900,
            'lrgprob': 4500 
        }
    },
    'cg_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'dirname' : 'cg',
        'exe': {
            'smlprob': './cg.B.x',
            'medprob': './cg.C.x',
            'lrgprob': './cg.D.x'
        },
        'timeout':{
            'smlprob': 100,
            'medprob': 300,
            'lrgprob': 3600
        }
    },
    'ft_nas': {
        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
        'dirname' : 'ft',
        'exe': {
            'smlprob': './ft.B.x',
            'medprob': './ft.C.x',
            'lrgprob': './ft.D.x'
        },
        'timeout':{
            'smlprob': 60,
            'medprob': 150,
            'lrgprob': 1800
        }
    },
#    'lu_nas': {
#        'xtime-regex':r'(?<=Time in seconds =)(\s*\d*\.\d*)(?=\s)',
#        'valid-regex':r'(Verification\s*=\s*SUCCESSFUL)(?=\s)',
#        'dirname' : 'lu',
#        'exe': {
#            'smlprob': './lu.B.x',
#            'medprob': './lu.C.x',
#            'lrgprob': './lu.D.x'
#        }
#    },
#    'bfs_rodinia': {
#        'xtime-regex':r'(?<=Compute time: )(\s*\d*\.\d*)(?=\s)',
#        'valid-regex':'',
#        'dirname' : 'bfs',
#        'exe': {
#            'smlprob': './bfs 1 ../inputs/graph4096.txt',
#            'medprob': './bfs 1 ../inputs/graph65536.txt',
#            'lrgprob': './bfs 1 ../inputs/graph1MW_6.txt'
#        },
#        'timeout':{
#            'smlprob': 10,
#            'medprob': 10,
#            'lrgprob': 10
#        }
#    },
    'cfd_rodinia': {
        'xtime-regex':r'(?<=Compute time: )(\s*\d*\.\d*)(?=\s)',
        'valid-regex':'',
        'dirname' : 'cfd',
        'exe': {
            'smlprob': './euler3d_cpu ../inputs/fvcorr.domn.097K',
            'medprob': './euler3d_cpu ../inputs/missile.domn.0.2M',
            'lrgprob': './euler3d_cpu ../inputs/missile.domn.0.4M'
        },
        'timeout':{
            'smlprob': 180,
            'medprob': 180,
            'lrgprob': 600
        }
    },
    'hpcg': {
        'xtime-regex':r'(?<=Benchmark Time Summary::Total=)(\d*\.\d*)(?=\s)',
        'valid-regex':r'(?<=Final Summary::)(Results are valid)(?=\s)',
        'dirname' : 'hpcg',
        'exe': {
            'smlprob': 'rm -f *.txt && ./xhpcg --nx=64 --ny=64 --nz=64',
            'medprob': 'rm -f *.txt && ./xhpcg --nx=128 --ny=128 --nz=128',
            'lrgprob': 'rm -f *.txt && ./xhpcg --nx=200 --ny=200 --nz=200'
        },
        'timeout':{
            'smlprob': 120,
            'medprob': 300,
            'lrgprob': 600
        }
    },
    'lulesh': {
        'xtime-regex':r'(?<=\()\s*(\d*\.\d*)(?= overall\))',
        'valid-regex':'',
        'dirname' : 'lulesh',
        'exe':{
            'smlprob': './lulesh2.0 -s 30 -r 100 -b 0 -c 8 -i 200',
            'medprob': './lulesh2.0 -s 55 -r 100 -b 0 -c 8 -i 200',
            'lrgprob': './lulesh2.0 -s 80 -r 100 -b 0 -c 8 -i 200',
        },
        'timeout':{
            'smlprob': 180,
            'medprob': 300,
            'lrgprob': 600
        },
        'regions':{
            'smlprob':[ 'lulesh.cc@1022', 'lulesh.cc@1097', 'lulesh.cc@1131', 'lulesh.cc@1162', 'lulesh.cc@1180',
                        'lulesh.cc@1211', 'lulesh.cc@1237', 'lulesh.cc@1537', 'lulesh.cc@1613', 'lulesh.cc@1649', 
                        'lulesh.cc@1803', 'lulesh.cc@2057', 'lulesh.cc@2066', 'lulesh.cc@2101', 'lulesh.cc@2116',
                        'lulesh.cc@2143', 'lulesh.cc@2161', 'lulesh.cc@2200', 'lulesh.cc@2236', 'lulesh.cc@2291', 
                        'lulesh.cc@2350', 'lulesh.cc@2394', 'lulesh.cc@2472', 'lulesh.cc@2522', 'lulesh.cc@2603', 
                        'lulesh.cc@283' , 'lulesh.cc@524' , 'lulesh.cc@570' , 'lulesh.cc@790' , 'lulesh.cc@979' ],
            'medprob':[ 'lulesh.cc@1022', 'lulesh.cc@1097', 'lulesh.cc@1131', 'lulesh.cc@1162', 'lulesh.cc@1180',
                        'lulesh.cc@1211', 'lulesh.cc@1237', 'lulesh.cc@1537', 'lulesh.cc@1613', 'lulesh.cc@1649', 
                        'lulesh.cc@1803', 'lulesh.cc@2057', 'lulesh.cc@2066', 'lulesh.cc@2101', 'lulesh.cc@2116',
                        'lulesh.cc@2143', 'lulesh.cc@2161', 'lulesh.cc@2200', 'lulesh.cc@2236', 'lulesh.cc@2291', 
                        'lulesh.cc@2350', 'lulesh.cc@2394', 'lulesh.cc@2472', 'lulesh.cc@2522', 'lulesh.cc@2603', 
                        'lulesh.cc@283' , 'lulesh.cc@524' , 'lulesh.cc@570' , 'lulesh.cc@790' , 'lulesh.cc@979' ],
            'lrgprob':[ 'lulesh.cc@1022', 'lulesh.cc@1097', 'lulesh.cc@1131', 'lulesh.cc@1162', 'lulesh.cc@1180',
                        'lulesh.cc@1211', 'lulesh.cc@1237', 'lulesh.cc@1537', 'lulesh.cc@1613', 'lulesh.cc@1649', 
                        'lulesh.cc@1803', 'lulesh.cc@2057', 'lulesh.cc@2066', 'lulesh.cc@2101', 'lulesh.cc@2116',
                        'lulesh.cc@2143', 'lulesh.cc@2161', 'lulesh.cc@2200', 'lulesh.cc@2236', 'lulesh.cc@2291', 
                        'lulesh.cc@2350', 'lulesh.cc@2394', 'lulesh.cc@2472', 'lulesh.cc@2522', 'lulesh.cc@2603', 
                        'lulesh.cc@283' , 'lulesh.cc@524' , 'lulesh.cc@570' , 'lulesh.cc@790' , 'lulesh.cc@979' ]
        }
    },
}
