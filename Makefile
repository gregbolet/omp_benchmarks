
.PHONY: all bfs bt cfd cg cholesky ft hpcg lu lulesh

all: bfs bt cfd cg cholesky ft hpcg lu lulesh

bfs:
	cd bfs; make;

bt:
	cd bt; make clean; make bt CLASS=C; 
	cd bt; make clean; make bt CLASS=D;
	cd bt; make clean; make bt CLASS=C APOLLO_BUILD=1; 
	cd bt; make clean; make bt CLASS=D APOLLO_BUILD=1;

cfd:
	cd cfd; make clean; make;

cg:
	cd cg; make clean; make cg CLASS=C; 
	cd cg; make clean; make cg CLASS=D;
	cd cg; make clean; make cg CLASS=C APOLLO_BUILD=1; 
	cd cg; make clean; make cg CLASS=D APOLLO_BUILD=1;

cholesky:
	echo ""

ft:
	cd ft; make clean; make ft CLASS=C; 
	cd ft; make clean; make ft CLASS=D;
	cd ft; make clean; make ft CLASS=C APOLLO_BUILD=1; 
	cd ft; make clean; make ft CLASS=D APOLLO_BUILD=1;

hpcg:
	cd hpcg; rm -rf buildNoApollo; mkdir -p buildNoApollo; cd buildNoApollo; ../configure LLVM_OMP_No_Apollo; make; cp ./bin/* ./;
	cd hpcg; rm -rf buildWithApollo; mkdir -p buildWithApollo; cd buildWithApollo; ../configure LLVM_OMP_With_Apollo; make; cp ./bin/* ./;

lu:
	cd lu; make clean; make lu CLASS=C; 
	cd lu; make clean; make lu CLASS=D;
	cd lu; make clean; make lu CLASS=C APOLLO_BUILD=1; 
	cd lu; make clean; make lu CLASS=D APOLLO_BUILD=1;

lulesh:
	cd lulesh; rm -rf buildNoApollo; mkdir -p buildNoApollo; cd buildNoApollo; ../runBuildNoApollo.sh; make;
	cd lulesh; rm -rf buildWithApollo; mkdir -p buildWithApollo; cd buildWithApollo; ../runBuildWithApollo.sh; make;






	