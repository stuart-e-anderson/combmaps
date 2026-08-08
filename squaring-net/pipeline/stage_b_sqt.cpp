// Stuart Anderson stuart.errol.anderson@gmail.com
// g++ -O3 -Wall -std=c++11 stage_b_sqt.cpp -o sqt -lboost_system -lboost_serialization -lm -lopenblas -llapack
// SQT (Squared Tiler) -
// squared square/rectangle finder, finds ciss siss spss cpss cpsr cisr spsr sisr;
// and tilings with zero edges, (called degenerates), and saves as canonical bouwkampcode
// version 4.3; date: 29th-Mar 2026
// latest version http://www.squaring.net/downloads
//
// SPEC-1 Stage B, the one allowed change: graph linkage. Every emitted line is
// now prefixed with the source graph's nauty canonical hash, read from a
// sidecar file <plantri_file>.hashes.txt (one hash per line, in the same
// order plantri emits graphs in <plantri_file> -- produced by Stage A's
// stage_a_driver.py). Solver, classifier and canonicaliser are untouched.

#include <algorithm>
#include <boost/numeric/ublas/io.hpp>
#include <boost/numeric/ublas/lu.hpp>
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>
#include <boost/numeric/ublas/triangular.hpp>
#include <boost/numeric/ublas/vector.hpp>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <exception>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <limits.h>
#include <list>
#include <map> 
#include <set>
#include <sstream>
#include <string>
#include <utility>
#include <vector>


namespace ublas = boost::numeric::ublas;
using namespace std;

long long gcd(long long n, long long m){return m==0?n:gcd(m,n%m);}

 #ifndef INVERT_MATRIX_HPP
 #define INVERT_MATRIX_HPP

 template<class T>
 double InvertMatrix (const ublas::matrix<T>& input, ublas::matrix<T>& inverse) {
	using namespace boost::numeric::ublas;
	typedef permutation_matrix<std::size_t> pmatrix;
	matrix<T> M(input);
	pmatrix pm(M.size1());
	int res = lu_factorize(M,pm);
		if( res != 0 ) return 0;
	double product = 1;
	for(unsigned int i = 0; i<M.size1(); i++)
	{
		product = product * M(i,i);
	}
	inverse.assign(ublas::identity_matrix<T>(M.size1()));
	lu_substitute(M, pm, inverse);
	return product;
 }

#endif //INVERT_MATRIX_HPP
 
// DEBUGGING FUNCTION (kept brief for profile clarity)
template<typename T>
void print_tiling_data(const std::string& caller_name, int s0, T s1, T s2,
                       const std::vector<T>& Size, const std::vector<T>& Top,
                       const std::vector<T>& Left, const std::vector<T>& Right,
                       const std::vector<T>& Bottom) {
    std::cout << "\n--- DEBUG OUTPUT: " << caller_name << " --- Tiling: " << s1 << "x" << s2 << "\n";
    // ... (rest of function omitted for brevity)
}

////////////////////////////////////////////////////////////////////////////////////////////////
void voltageG(vector < vector <long long> >& GraphDual, unsigned int e)
{
    unsigned int edge = e;
    do { 
        if((GraphDual.at(edge).at(9) == -1)&&(GraphDual.at(edge).at(6)>= 0)) {
            GraphDual.at(edge).at(8) = GraphDual.at(e).at(8);
            GraphDual.at(edge).at(9) = GraphDual.at(e).at(8) - GraphDual.at(edge).at(6);
            
            for (unsigned int a = 0; a < GraphDual.size(); a++) {
                for (unsigned int b = 0; b < GraphDual.size(); b++) {
                    if ((GraphDual.at(b).at(0)==GraphDual.at(a).at(1))&&(GraphDual.at(b).at(8) == -1)) {
                        GraphDual.at(b).at(8) = GraphDual.at(a).at(9);
                    }
                }
            } 
            voltageG(GraphDual, GraphDual.at(edge).at(2));
        } 
        edge = GraphDual.at(edge).at(12);
    } while (edge != e) ;
}

void voltageD(vector < vector <long long> >& GraphDual, unsigned int e)
{
    unsigned int edge = e;
    do { 
        if((GraphDual.at(edge).at(11) == -1)&&(GraphDual.at(edge).at(7)>= 0)) {
            GraphDual.at(edge).at(10) = GraphDual.at(e).at(10);
            GraphDual.at(edge).at(11) = GraphDual.at(e).at(10) - GraphDual.at(edge).at(7);
            for (unsigned int a = 0; a < GraphDual.size(); a++) {
                for (unsigned int b = 0; b < GraphDual.size(); b++) {
                    if ((GraphDual.at(b).at(3)==GraphDual.at(a).at(4))&&(GraphDual.at(b).at(10) == -1)) {
                        GraphDual.at(b).at(10) = GraphDual.at(a).at(11);
                    }
                }
            } 
            voltageD(GraphDual, GraphDual.at(edge).at(2));
        } 
        edge = GraphDual.at(edge).at(5);
    } while (edge != e) ;
}

bool simple_compound_test(int s0, int s1, int s2, vector<long long> Size, vector<long long> Top, vector<long long> Left, vector<long long> Right, vector<long long> Bottom) {
    // NOTE: Full function body is included here to ensure single-file compilation.
    reverse(Top.begin(), Top.end());
    reverse(Left.begin(), Left.end());
    reverse(Right.begin(), Right.end());
    reverse(Bottom.begin(), Bottom.end());
    reverse(Size.begin(), Size.end());
    Size.push_back(s2);
    Size.push_back(s1);
    Size.push_back(s0);
    for(unsigned int y = 0; y<3;y++) {
        Top.push_back(0);
        Left.push_back(0);
        Right.push_back(0);
        Bottom.push_back(0);
    }
    reverse(Top.begin(), Top.end());
    reverse(Left.begin(), Left.end());
    reverse(Right.begin(), Right.end());
    reverse(Bottom.begin(), Bottom.end());
    reverse(Size.begin(), Size.end());
    Size.push_back(Size.at(1));
    Top.push_back(0);
    Left.push_back(0);
    Right.push_back(Size.at(1));
    Bottom.push_back(Size.at(1));
    bool comp;
    long long top, left, right, bottom; int squares, rectangles;
    top = 0;
    left = 0;
    right = 0;
    bottom = 0;
    squares = 0;
    rectangles = 0;
    bool sw = false;
    bool ne = false;

    // --- SPARSE INTERVAL CHECK ---
    
    for (unsigned int k = 3; k< Size.size()-1; k++){
        top = Top.at(k);
        left = Left.at(k); // set north west corner, 
        for (unsigned int l = 3; l< Size.size()-1; l++){
            if ((Right.at(l) > left)&& (Bottom.at(l) > top) ){
                right = Right.at(l);
                bottom = Bottom.at(l);  //set south east corner
                for (unsigned int m= 3; m< Size.size()-1; m++){	
                    if((Left.at(m) == left)&&(Bottom.at(m) == bottom)){
                        //south west corner exists
                        sw = true;
                    }
                    if ((Top.at(m) ==top)&&(Right.at(m) == right)){
                        //north east corner exists
                        ne = true;
                        }
                    }
                    // if corners exist, test edges
                    if( (ne == true) && (sw == true)) {
                        long long limit_r = std::min(right, Size.at(1));
                        long long limit_b = std::min(bottom, Size.at(2));
                        bool TopExists = true;
                        bool RightExists = true;
                        bool BottomExists = true;
                        bool LeftExists = true;

                        // Optimization: Short-circuit for atomic elements (k==l)
                        if (k != l) {
                            // COMPOSITE: Perform Sparse Checks
                            
                            // --- SPARSE CHECK 1: TOP EDGE (Horizontal) ---
                            {
                                std::vector<std::pair<long long, long long>> intervals;
                                for (unsigned int q = 3; q < Size.size() - 1; q++) {
                                    if (Top.at(q) == top) { // Overlaps top line
                                        long long s = std::max(Left.at(q), left);
                                        long long e = std::min(Right.at(q), limit_r);
                                        if (s < e) intervals.push_back(std::make_pair(s, e));
                                    }
                                }
                                std::sort(intervals.begin(), intervals.end());
                                long long curr = left;
                                for (size_t i = 0; i < intervals.size(); ++i) {
                                    if (intervals[i].first > curr) { TopExists = false; break; }
                                    curr = std::max(curr, intervals[i].second);
                                }
                                if (curr < limit_r) TopExists = false;
                            }

                            // --- SPARSE CHECK 2: RIGHT EDGE (Vertical) ---
                            if(TopExists) {
                                std::vector<std::pair<long long, long long>> intervals;
                                for (unsigned int q = 3; q < Size.size() - 1; q++) {
                                    if (Right.at(q) == right) {
                                        long long s = std::max(Top.at(q), top);
                                        long long e = std::min(Bottom.at(q), limit_b);
                                        if (s < e) intervals.push_back(std::make_pair(s, e));
                                    }
                                }
                                std::sort(intervals.begin(), intervals.end());
                                long long curr = top;
                                for (size_t i = 0; i < intervals.size(); ++i) {
                                    if (intervals[i].first > curr) { RightExists = false; break; }
                                    curr = std::max(curr, intervals[i].second);
                                }
                                if (curr < limit_b) RightExists = false;
                            }

                            // --- SPARSE CHECK 3: BOTTOM EDGE (Horizontal) ---
                            if(TopExists && RightExists) {
                                std::vector<std::pair<long long, long long>> intervals;
                                for (unsigned int q = 3; q < Size.size() - 1; q++) {
                                    if (Bottom.at(q) == bottom) {
                                        long long s = std::max(Left.at(q), left);
                                        long long e = std::min(Right.at(q), limit_r);
                                        if (s < e) intervals.push_back(std::make_pair(s, e));
                                    }
                                }
                                std::sort(intervals.begin(), intervals.end());
                                long long curr = left;
                                for (size_t i = 0; i < intervals.size(); ++i) {
                                    if (intervals[i].first > curr) { BottomExists = false; break; }
                                    curr = std::max(curr, intervals[i].second);
                                }
                                if (curr < limit_r) BottomExists = false;
                            }

                            // --- SPARSE CHECK 4: LEFT EDGE (Vertical) ---
                            if(TopExists && RightExists && BottomExists) {
                                std::vector<std::pair<long long, long long>> intervals;
                                for (unsigned int q = 3; q < Size.size() - 1; q++) {
                                    if (Left.at(q) == left) {
                                        long long s = std::max(Top.at(q), top);
                                        long long e = std::min(Bottom.at(q), limit_b);
                                        if (s < e) intervals.push_back(std::make_pair(s, e));
                                    }
                                }
                                std::sort(intervals.begin(), intervals.end());
                                long long curr = top;
                                for (size_t i = 0; i < intervals.size(); ++i) {
                                    if (intervals[i].first > curr) { LeftExists = false; break; }
                                    curr = std::max(curr, intervals[i].second);
                                }
                                if (curr < limit_b) LeftExists = false;
                            }
                        } // End else (Composite check)

                        // --- COUNTING LOGIC ---
                        if (TopExists && RightExists && BottomExists && LeftExists) {
                            if ( (bottom - top) == (right - left) ){
                                // It is a Square (Atomic or Composite)
                                squares++;
                            } else {
                                // It is a Rectangle (Atomic or Composite)
                                rectangles++;
                            }
                        }
                        } // if ne && sw
                    ne = false;
                    sw = false;				   		
                    } //next se corner
                    
                } //iterate over Size se corner
            } //iterate over Size nw corner
        //}	
        
        if (((squares==Size.at(0))&&(rectangles==1))||((squares==Size.at(0)+1)&&(rectangles==0))){
                comp = false;
                } else {
                comp = true;
        }
        squares = 0;
        rectangles = 0;
        Top.clear() ;
        Bottom.clear() ;
        Left.clear();
        Right.clear() ;
        Size.clear() ;
        return comp;
}


int main (int argc, char* argv[]){
    std::clock_t start_total;
    double duration_total;
    start_total = std::clock();

    bool do_simples = false; bool do_compounds = false; bool do_perfects = false;
    bool do_imperfects = false; bool do_rectangles = false; bool do_squares = false ;
    string plantri_file;
    
    // ... (Argument parsing) ...
    if (argc == 1)
    {
        cout<<endl;
        cout <<"SQT (Squared Tiler)  by Stuart Anderson, "<<endl;
        cout <<"  ========================================================="<<endl;
        cout <<"  stuart.errol.anderson@gmail.com"<<endl;
        cout <<"  Latest version http://www.squaring.net/downloads/sqt-bk2ps-bk2svg.zip"<<endl;
        cout <<"  This version; v4.3 22th March 2026"<<endl;
        cout <<"  "<<endl;
        cout <<"  Squared rectangles and squared squares are dissections of rectangles and squares "<<endl;
        cout <<"  into smaller squares of integer size, called the elements."<<endl;
        cout <<"  "<<endl;
        cout <<"  The number of elements is finite and is called the order of the dissection.  "<<endl;
        cout <<"  "<<endl;
        cout <<"  In a dissection there are no gaps or overlaps between the elements, and the sum of the area"<<endl;
        cout <<"  of the elements in a dissection equals the area of the dissection, equal to width x height"<<endl;
        cout <<"  "<<endl;
        cout <<"  Squared squares and squared rectangles are classified into simple or compound,"<<endl;
        cout <<"  and perfect or imperfect; Compound dissections contain a smaller squared square"<<endl;
        cout <<"  or squared rectangle, simples do not. Perfect dissections have all squares "<<endl;
        cout <<"  different sizes, imperfects allow squares the same size.  The name is a misnomer,"<<endl;
        cout <<"  imperfect tilings can contain symmetries which dont appear in 'perfect' tilings."<<endl;
        cout <<"  "<<endl;
        cout <<"  The program sqt generates squared squares and squared rectangles from 2 and "<<endl;
        cout <<"  3-connected planar map files which are generated by the program plantri."<<endl;
        cout <<"  Plantri is by Gunnar Brinkmann and Brendan McKay and is available from"<<endl;
        cout <<"  http://cs.anu.anu.edu.au/~bdm/plantri/ ."<<endl;
        cout <<"  The program sqt uses long longs for integer currents, voltages, element sizes and "<<endl;
        cout <<"  double precision for matrix operations and should be accurate for processing graphs "<<endl;
        cout <<"  with up to 70 edges (order 69).  The program bk2ps can be used to view dissections up to order 46 only "<<endl;
        cout <<"  due to the Postscript 32 bit integer size limit. bk2svg uses SVG double-precision and can be used"<<endl;
        cout <<"  for much larger dissections."<<endl;
        cout <<"  compile line; g++ -o sqt sqt.cpp -lboost_system -lboost_serialization -lm -std=c++11 -O3 -lopenblas -llapack"<<endl;
        cout <<"  Boost numeric ublas library headers are required. sqt has the following options and combinations "<<endl;
        cout <<"  "<<endl;
        cout <<"  Syntax is: sqt -scpirS filename.  Options are optional, in any order, before the plantri filename."<<endl;
        cout <<"  s (lower case) for simples"<<endl;
        cout <<"  c for compounds "<<endl;
        cout <<"  p for perfects"<<endl;
        cout <<"  i for imperfects"<<endl;
        cout <<"  r for rectangles"<<endl;
        cout <<"  S (upper case) for squares"<<endl;
        cout <<"  If no arguments are given, default options used are -cspiS"<<endl;
        cout <<"  i.e. ciss, siss, spss, cpss. This collection of dissections are the most general kind of squared square,"<<endl;
        cout <<"  also known as Mrs Perkins's quilts."<<endl;
        cout <<"  Dissections which include degenerate solutions of zero edges are saved to a separate degenerates file "<<endl;
        cout <<"  "<<endl;
        cout <<"  The output is saved as tablecode. Tablecode is bouwkampcode with only blank space and integers."<<endl;
        cout <<"  Rectangular dissections can be reflected and rotated, the code for only one representative is chosen."<<endl;
        cout <<"  The code for the rectangle with the largest corner square in the top left square is the canonical code."<<endl;
        cout <<"  Canonical code for a squared square requires another comparison with the top left corner boundary squares."<<endl;
        cout <<"  Format is ; order, width, height followed by the elements listed from left to right and top to bottom."<<endl;
        cout <<"  Tablecode output files are named with the input filename, a dash '-',"<<endl;
        cout <<"  and letters s or c and p or i followed by ss for squared squares or sr for squared rectangles."<<endl;
        cout <<"  To view the dissections, download bk2ps and/or bk2svg, compile and run with bouwkampcode "<<endl;
        cout <<"  filename as input, and choose the number of dissections per postscript A4 page."<<endl;
        cout << " "<< endl;

        return 0;
    }
    else if (argc == 2)
    {
        plantri_file = argv[1];
        do_simples = true;
        do_compounds = true;
        do_perfects = true;
        do_imperfects = true;
        do_squares = true;
        do_rectangles = false;
    }
    else if (argc == 3)
    {
        plantri_file = argv[2];
        string args = argv[1];
        if (args.find_first_of("-")!=string::npos)
        {
            // FIX 1: Strict S/s separation, but allow r/R for rectangles
            if (args.find_first_of("s")!=string::npos) do_simples = true;    // Lowercase s = Simples
            if (args.find_first_of("c")!=string::npos) do_compounds = true;
            if (args.find_first_of("p")!=string::npos) do_perfects = true;
            if (args.find_first_of("i")!=string::npos) do_imperfects = true;
            if (args.find_first_of("rR")!=string::npos) do_rectangles = true; // Allow r OR R
            if (args.find_first_of("S")!=string::npos) do_squares = true;     // Uppercase S = Squares

            // Disable flags if missing from valid string
            if (args.find_first_of("s")==string::npos) do_simples = false;
            if (args.find_first_of("c")==string::npos) do_compounds = false;
            if (args.find_first_of("p")==string::npos) do_perfects = false;
            if (args.find_first_of("i")==string::npos) do_imperfects = false;
            if (args.find_first_of("rR")==string::npos) do_rectangles = false; // Check r OR R
            if (args.find_first_of("S")==string::npos) do_squares = false;
        } else { 
            cout<<"  Syntax is: sqt -scpirS filename"<<endl;
            cout<<"  type 'sqt', 'enter' for program information "<<endl;
            }
    }

    ifstream File(plantri_file.c_str(), ios::in | ios::binary);
    if (!File) { // check it opened ok
        std::cerr << "Cannot open file "<< plantri_file<< " \n";
    }

    cout<<"  processing plantri file "<<plantri_file<<"   ..."<<endl;
    int n=0; int v=0;unsigned int e=0; int f=0; int g =0 ;
    char c;
    string line ="";
    vector< vector<unsigned int> > graph;
    vector<unsigned int> edges;
    
    // tablecode -> source graph's nauty canonical hash (SPEC-1 Stage B graph linkage);
    // map::emplace only inserts on first sight of a key, preserving the prior std::set dedup semantics
    map <string, string> spss;
    map <string, string> spsr; map <string, string> siss; map <string, string> sisr; map <string, string> cpss; map <string, string> cpsr; map <string, string> ciss;
    map <string, string> cisr;
    map <string, string> degenerate_codes;
    vector<string> written_files;

    string hash_sidecar_file = plantri_file + ".hashes.txt";
    vector<string> graph_hashes;
    {
        ifstream hf(hash_sidecar_file.c_str());
        if (!hf) {
            cerr << "FATAL: graph hash sidecar not found: " << hash_sidecar_file << endl;
            cerr << "  sqt requires <plantri_file>.hashes.txt (one nauty canonical hash per graph," << endl;
            cerr << "  in plantri file order) per SPEC-1 Stage B's graph-linkage contract." << endl;
            return 1;
        }
        string hash_line;
        while (getline(hf, hash_line)) {
            if (!hash_line.empty()) graph_hashes.push_back(hash_line);
        }
    }
    string current_graph_hash;

    File.seekg(15, ios::beg);
    for(;;) {
        graph.clear(); 
        edges.clear();
        e = 0;
        
        if(File.read (&c, 1)) {
            g++;
            if ((size_t)(g - 1) >= graph_hashes.size()) {
                cerr << "FATAL: graph " << g << " in " << plantri_file
                     << " has no entry in " << hash_sidecar_file
                     << " (sidecar has " << graph_hashes.size() << " hashes)" << endl;
                return 1;
            }
            current_graph_hash = graph_hashes[g - 1];
            n = (unsigned char) c;
            graph.reserve(n);
            for (int i = 0; i<n ; i++) { 
                if(File.read (&c, 1)) {
                    v = (unsigned char) c;
                    e++;
                    edges.push_back(v);
                    while (v!=0) {
                        if(File.read (&c, 1)) {
                            v = (unsigned char) c;
                            if (v!=0) { 
                            edges.push_back(v);
                            e++;
                            }                   
                        }
                        else {
                                cout<<"read file "<<argv[2]<<" failed on:"<<" graph; "<<g<<" vertex; "<<v<<" edge; "<<e<<endl;
                                break;
                               }
                    }
                    graph.push_back(edges);
                    edges.clear();
                }
                else {
                    cout<<" read file failed"<<endl;
                    break;
                }
            }
        }
        else {
                // --- FIX 2: REORDERED EOF PROCESSING ---
                if (File.eof()){
                    cout<<"end of file "<<plantri_file<<endl;
                } else {
                    cout <<"check filename, "<<plantri_file<<" and file location"<<endl;
                }

                // 1. WRITE FILES FIRST (Populate written_files)
                std::ostringstream ous;
                std::ofstream bkcanon_file;
                
                if (!spss.empty()) {
                    ous << plantri_file << "-" << "spss.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : spss) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!spsr.empty()) {
                    ous << plantri_file << "-" << "spsr.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : spsr) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!siss.empty()) {
                    ous << plantri_file << "-" << "siss.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : siss) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!sisr.empty()) {
                    ous << plantri_file << "-" << "sisr.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : sisr) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!cpss.empty()) {
                    ous << plantri_file << "-" << "cpss.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : cpss) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!cpsr.empty()) {
                    ous << plantri_file << "-" << "cpsr.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : cpsr) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!ciss.empty()) {
                    ous << plantri_file << "-" << "ciss.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : ciss) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!cisr.empty()) {
                    ous << plantri_file << "-" << "cisr.txt";
                    bkcanon_file.open(ous.str().c_str(), std::ios::out);
                    for (const auto& kv : cisr) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }
                if (!degenerate_codes.empty()) {
                    ous << plantri_file << "-" << "degenerate.txt";
                    bkcanon_file.open (ous.str().c_str(), std::ios::out);
                    for (const auto& kv : degenerate_codes) bkcanon_file << kv.second << " " << kv.first;
                    bkcanon_file.close();
                    written_files.push_back(ous.str());
                    ous.str(""); ous.clear();
                }

                // 2. PRINT SUMMARY AND FILENAMES (Now that files exist)
                cout << "In file "<<plantri_file <<" "<<g<<" graphs were processed to find;" <<  endl;
                
                if ((do_simples==true)&&(do_perfects==true)&&(do_squares==true)) cout << spss.size() << " simple perfect squared squares;"<<endl;
                if ((do_simples==true)&&(do_perfects==true)&&(do_rectangles==true)) cout << spsr.size() << " simple perfect squared rectangles;"<<endl;
                if ((do_simples==true)&&(do_imperfects==true)&&(do_squares==true)) cout << siss.size() << " simple imperfect squared squares;"<<endl;
                if ((do_simples==true)&&(do_imperfects==true)&&(do_rectangles==true)) cout << sisr.size() << " simple imperfect squared rectangles;"<<endl;
                if ((do_compounds==true)&&(do_perfects==true)&&(do_squares==true)) cout << cpss.size() << " compound perfect squared squares;"<<endl;
                if ((do_compounds==true)&&(do_perfects==true)&&(do_rectangles==true)) cout << cpsr.size() << " compound perfect squared rectangles;"<<endl;
                if ((do_compounds==true)&&(do_imperfects==true)&&(do_squares==true)) cout << ciss.size() << " compound imperfect squared squares;"<<endl;
                if ((do_compounds==true)&&(do_imperfects==true)&&(do_rectangles==true)) cout << cisr.size() << " compound imperfect squared rectangles."<<endl;
                if (!degenerate_codes.empty()) cout << degenerate_codes.size() << " degenerate (zero-edge) tilings found." << endl;

                if (!written_files.empty()) {
                    cout << "\n  Output files written:\n";
                    for (const auto& f : written_files) {
                        cout << "    " << f << endl;
                    }
                }
            
                break; // End Infinite Loop
        }

        // --- TIMING VARIABLES ---
        std::chrono::high_resolution_clock::time_point start_time, end_time;
        std::chrono::duration<double> time_matrix, time_link, time_solve, time_check;

        f = e/2 - n + 2;
        vector< vector< unsigned int> >::size_type uu;
        vector< unsigned int>::size_type vv;
        e = e/2;
        
        static const int FP64_EDGE_WARN  = 70;
        static bool warned_fp64 = false;
        if (e >= FP64_EDGE_WARN && !warned_fp64) {
            std::cout << "\n  [WARNING] Graph with " << e << " edges detected.\n";
            std::cout << "  Graphs with 70 or more edges stretch 64-bit double precision math to its limits.\n";
            std::cout << "  Matrix inversions may lose precision, potentially resulting in invalid tilings.\n\n";
            warned_fp64 = true; // Set to true so we only warn once per run
        }
     
        ublas::matrix<double> Aa(e,n);
        ublas::matrix<double> K(n-1,n-1);
        ublas::matrix<double> V(n-1,n-1);
        ublas::matrix<double> F(e,e); 
        ublas::matrix<double> T(n-1,e);
        ublas::vector<double> R(e); 
        ublas::matrix<double> B(e,e); 
        ublas::matrix<double> m(e,e);
        unsigned int i = 0;
        Aa.clear();
        
        // 1. MATRIX GENERATION
        start_time = std::chrono::high_resolution_clock::now();
        
        for (unsigned int uu = 0; uu < graph.size(); uu++) { 
            for (unsigned int vv = 0; vv < graph[uu].size(); vv++) { 
                if (uu+1<graph[uu][vv]) { 
                    Aa(i,uu) = 1;             
                    Aa(i,graph[uu][vv]-1) = -1;
                    i++;
                } 
            }
        }
        i = 0;

        ublas::matrix_range<ublas::matrix<double> > A(Aa, ublas::range(0,e),ublas::range(1,n));
        T = ublas::trans(A);
        K = prod( T, A );
        double det = InvertMatrix(K , V);
        V = round(det)*V;
        m = prod( A, V );
        F = prod( m, T );
        for(unsigned int i=0; i<(e); i++)
        {
            if (round(F(i,i))!= 0){
                R[i] = abs(gcd(round(F(i,0)),round( F(i,1))));
                }
            else R[i]=1;
            for (unsigned int j=1; j<e; j++){
                if (round(F(i,j))!= 0){
                    R[i] = abs(gcd(round(R[i]), round(F(i,j))));
                 }
              }
        }

        for(unsigned int i=0; i<e; i++)
        {
            for(unsigned int j=0; j<e; j++)
            {
            B(i,j) = round(F(i,j))/R[i];
                if (abs(B(i,j))<0.0001) B(i,j) = 0.0;
            }       
        }
        end_time = std::chrono::high_resolution_clock::now();
        time_matrix = end_time - start_time;

        long long s2 = 0;
        long long s1 = 0;
        bool is_compound;
        bool is_square;
        bool is_perfect;
        
        for(unsigned int i=0; i<e; i++)        {
            s1 = (long long)round(B(i,i));
            s2 = (long long)(round(det)/round(R[i])) - s1;

            if (s1 <= 0 || s2 <= 0) {
                continue;
            } 

            bool has_zero_edges_flag = false;
            if (s1 == s2 ) { 
                is_square = true;
            } else {
                is_square = false;
            }
            list<long long> Currents;
            for(unsigned int j=0; j<e; j++){  
                Currents.push_back((long long)abs(B(i,j)));
            }
            
            Currents.sort();
            Currents.unique();
            if (Currents.size() == e) { 
                is_perfect = true;
            }
            else {                      
                is_perfect = false;
            }
            
            if (( ((is_square == true )&&(do_squares == true)) || ((is_square == false)&&(do_rectangles == true)) || ((is_perfect==true)&&(do_perfects==true)) || ((is_perfect==false)&&(do_imperfects==true)) ))
            { 
                start_time = std::chrono::high_resolution_clock::now();
                
                vector< vector<long long> > GraphDual;
                vector<long long> str; 
                GraphDual.reserve(e); 
                str.reserve(13);

                std::map<long long, int> edge_lookup;
                long long MAX_V = graph.size() + 2; 
                std::vector<int> vertex_start_idx(n + 1, -1);

                int current_edge_idx = 0;
                for (unsigned int u_idx = 0; u_idx < graph.size(); u_idx++) {
                    long long u = u_idx + 1;
                    vertex_start_idx[u] = current_edge_idx;
                    
                    for (unsigned int v_idx = 0; v_idx < graph[u_idx].size(); v_idx++) {
                        long long v = graph[u_idx][v_idx];
                        
                        str.clear();
                        str.push_back(u);       // 0: Source
                        str.push_back(v);       // 1: Target
                        str.push_back(-1);      // 2: Reversal Index (Pending)
                        str.push_back(0);       // 3: Dual Source (Face L)
                        str.push_back(0);       // 4: Dual Target (Face R)
                        str.push_back(-1);      // 5: Next Cyclic Edge (Pending)
                        str.push_back(0);       // 6: Current
                        str.push_back(0);       // 7: Dual Current
                        str.push_back(-1);      // 8: V src
                        str.push_back(-1);      // 9: V tgt
                        str.push_back(-1);      // 10: V dual src
                        str.push_back(-1);      // 11: V dual tgt
                        str.push_back(-1);      // 12: Cyclic Adj (Pending)
                        
                        GraphDual.push_back(str);
                        edge_lookup[u * MAX_V + v] = current_edge_idx;
                        current_edge_idx++;
                    }
                }

                for (unsigned int i = 0; i < GraphDual.size(); i++) {
                    long long u = GraphDual[i][0];
                    long long v = GraphDual[i][1];

                    if (edge_lookup.count(v * MAX_V + u)) {
                        GraphDual[i][2] = edge_lookup[v * MAX_V + u];
                    } 

                    if (i + 1 < GraphDual.size() && GraphDual[i+1][0] == u) {
                        GraphDual[i][12] = i + 1;
                    } else {
                        if (vertex_start_idx[u] != -1) {
                            GraphDual[i][12] = vertex_start_idx[u];
                        } else {
                            GraphDual[i][12] = i; 
                        }
                    }
                }

                for (unsigned int i = 0; i < GraphDual.size(); i++) {
                    long long rev_idx = GraphDual[i][2];
                    if (rev_idx != -1) {
                        GraphDual[i][5] = GraphDual[rev_idx][12];
                    }
                }
                
                bool graph_broken = false;
                for (unsigned int i = 0; i < GraphDual.size(); i++) {
                    if (GraphDual[i][2] == -1 || GraphDual[i][5] == -1) {
                        graph_broken = true;
                        break; 
                    }
                }
     
                if (graph_broken) {
                    GraphDual.clear();
                    continue; 
                }
                
                int c = 0;
                for (unsigned int a = 0; a < GraphDual.size(); a++) {
                    unsigned int thisedge = a;
                    if (GraphDual.at(thisedge).at(3) == 0) {
                        c++;
                        while (GraphDual.at(thisedge).at(3) == 0) {
                            GraphDual.at(thisedge).at(3) = c; 
                            thisedge = GraphDual.at(thisedge).at(5);
                        }
                    }
                }
                for (unsigned int a = 0; a < GraphDual.size(); a++) {
                    GraphDual.at(a).at(4) = GraphDual.at(GraphDual.at(a).at(2)).at(3);
                }

                vector< vector<unsigned int> > dual;
                dual.reserve(f); 
                for (int t = 0; t < c; t++) { 
                    unsigned int thisedge = 0;
                    for (unsigned int a = 0; a < GraphDual.size(); a++) {
                        if (GraphDual.at(a).at(3) == (t + 1)) {
                            thisedge = a;
                            break;
                        }
                    }
                    
                    vector<unsigned int> face_edges;
                    unsigned int start_edge = thisedge;
                    do {
                        edges.push_back(GraphDual.at(thisedge).at(4)); 
                        thisedge = GraphDual.at(thisedge).at(5);
                    } while (thisedge != start_edge);
                    
                    dual.push_back(edges);
                    edges.clear();
                }
                end_time = std::chrono::high_resolution_clock::now();
                time_link = end_time - start_time;
                
                start_time = std::chrono::high_resolution_clock::now();

                unsigned int ecount=0;
                unsigned int dcount=0;
                unsigned int edgeindx=0;

                for (uu = 0; uu < graph.size(); uu++) { 
                    for (vv = 0; vv < graph[uu].size(); vv++) { 
                        if (uu+1<graph[uu][vv]) { 
                            if(i == ecount) {
                                GraphDual.at(dcount).at(6) = s1;
                                GraphDual.at(GraphDual.at(dcount).at(2)).at(6) = -s1;
                                GraphDual.at(dcount).at(7) = s2; 
                                GraphDual.at(GraphDual.at(dcount).at(2)).at(7) = -s2;
                                GraphDual.at(dcount).at(8) = s1; 
                                GraphDual.at(dcount).at(10) = s2;
                                edgeindx = dcount;
                                } else {
                                GraphDual.at(dcount).at(6) = B(i,ecount);
                                GraphDual.at(GraphDual.at(dcount).at(2)).at(6) = -B(i,ecount);
                                GraphDual.at(dcount).at(7) = -B(i,ecount);
                                GraphDual.at(GraphDual.at(dcount).at(2)).at(7) = B(i,ecount);
                            }
                            ecount++;
                                }
                            dcount++;
                        }
                } 

                voltageG(GraphDual, edgeindx);
                voltageD(GraphDual, edgeindx);

                vector<long long> x;
                vector<long long> y;
                vector<long long> s;
                s.push_back(e-1);
                s.push_back(s1);
                s.push_back(s2);
                for (unsigned int a = 0; a< GraphDual.size(); a++) {
                    if ((GraphDual.at(a).at(6)>=0)&&(a!=edgeindx)){
                        x.push_back(GraphDual.at(a).at(8));
                        y.push_back(GraphDual.at(a).at(10));
                        s.push_back(GraphDual.at(a).at(6));
                    }
                }
                s.at(0) = s.size()-3;
                
                if (s.size() <= 3) {
                    continue;
                }

                for (unsigned int a = 0; a < GraphDual.size(); a++) {
                    GraphDual.at(a).at(8)= -1;
                    GraphDual.at(a).at(9)= -1;
                    GraphDual.at(a).at(10)= -1;
                    GraphDual.at(a).at(11)= -1;
                }
                std::vector<long long> Top ;
                std::vector<long long> Bottom ;
                std::vector<long long> Left;
                std::vector<long long> Right ;
                std::vector<long long> Size ;

                for (unsigned int j = 0; j <  s.size()-3; j++){ 
                    Right.push_back(x[j]);
                    Left.push_back(x[j] - s[j+3]);
                    Top.push_back(y[j]);
                    Bottom.push_back(y[j] + s[j+3]);
                    Size.push_back(s[j+3]);
                }
                end_time = std::chrono::high_resolution_clock::now();
                time_solve = end_time - start_time;

                start_time = std::chrono::high_resolution_clock::now();

                has_zero_edges_flag = false;
                for (long long s_val : Size) {
                    if (s_val == 0) {
                        has_zero_edges_flag = true;
                        break;
                    }
                }

                is_compound = simple_compound_test(s.at(0), s1, s2, Size, Top, Left, Right, Bottom);
                
                if (!has_zero_edges_flag) {
                    if (((is_compound == true)&&(do_compounds == false))||((is_compound == false)&&(do_simples == false))) {continue;}
                }

                std::vector<long long> sortedTop(Top);
                std::vector<long long> sortedLeft(Left);
                std::vector<long long> sortedRight(Right);
                std::vector<long long> sortedBottom(Bottom);
                
                std::sort(sortedTop.begin(), sortedTop.end());
                std::sort(sortedLeft.begin(), sortedLeft.end());
                std::sort(sortedRight.begin(), sortedRight.end());
                std::sort(sortedBottom.begin(), sortedBottom.end());
                
                sortedTop.erase( std::unique( sortedTop.begin(),sortedTop.end() ), sortedTop.end() );
                sortedLeft.erase( std::unique( sortedLeft.begin(),sortedLeft.end() ), sortedLeft.end() );
                sortedRight.erase( std::unique( sortedRight.begin(),sortedRight.end() ), sortedRight.end() );
                sortedBottom.erase( std::unique( sortedBottom.begin(),sortedBottom.end() ), sortedBottom.end() );
                
                std::vector<long long> compBkcode;
                std::vector<std::vector<long long> > bkCodes;

                const size_t expected_len = Size.size() + 3;
                auto push_variant = [&](std::vector<long long>& v){
                    if (v.size() == expected_len) bkCodes.push_back(v);
                    v.clear();
                };

                compBkcode.push_back(s.at(0));
                compBkcode.push_back(s.at(1)); compBkcode.push_back(s.at(2));  
                for (unsigned int p=0; p < sortedTop.size(); p++){ for (unsigned int q=0; q < sortedLeft.size(); q++){ for (unsigned int r=0; r < Size.size(); r++){ if((sortedTop.at(p)==Top.at(r))&&(sortedLeft.at(q)==Left.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(1)); compBkcode.push_back(s.at(2));
                for (unsigned int p=0; p < sortedTop.size(); p++){ for ( auto qit = sortedRight.rbegin() ; qit != sortedRight.rend(); ++qit ) { for (unsigned int r=0; r < Size.size(); r++){ if((sortedTop.at(p)==Top.at(r))&&(*qit==Right.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(1)); compBkcode.push_back(s.at(2));
                for ( auto pit = sortedBottom.rbegin() ; pit != sortedBottom.rend(); ++pit ) { for ( auto qit = sortedRight.rbegin() ; qit != sortedRight.rend(); ++qit ) { for (unsigned int r=0; r < Size.size(); r++){ if((*pit==Bottom.at(r))&&(*qit==Right.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(1)); compBkcode.push_back(s.at(2));
                for ( auto pit = sortedBottom.rbegin() ; pit != sortedBottom.rend(); ++pit ) { for (unsigned int q=0; q < sortedLeft.size(); q++){ for (unsigned int r=0; r < Size.size(); r++){ if((*pit==Bottom.at(r))&&(sortedLeft.at(q)==Left.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(2)); compBkcode.push_back(s.at(1));
                for (unsigned int q=0; q < sortedLeft.size(); q++){ for (unsigned int p=0; p < sortedTop.size(); p++){ for (unsigned int r=0; r < Size.size(); r++){ if((sortedTop.at(p)==Top.at(r))&&(sortedLeft.at(q)==Left.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(2)); compBkcode.push_back(s.at(1));
                for ( auto qit = sortedRight.rbegin() ; qit != sortedRight.rend(); ++qit ) { for (unsigned int p=0; p < sortedTop.size(); p++){ for (unsigned int r=0; r < Size.size(); r++){ if((sortedTop.at(p)==Top.at(r))&&(*qit==Right.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(2)); compBkcode.push_back(s.at(1));
                for ( auto qit = sortedRight.rbegin() ; qit != sortedRight.rend(); ++qit ) { for ( auto pit = sortedBottom.rbegin() ; pit != sortedBottom.rend(); ++pit ) { for (unsigned int r=0; r < Size.size(); r++){ if((*pit==Bottom.at(r))&&(*qit==Right.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                compBkcode.push_back(s.at(0)); compBkcode.push_back(s.at(2)); compBkcode.push_back(s.at(1));
                for (unsigned int q=0; q < sortedLeft.size(); q++){ for ( auto pit = sortedBottom.rbegin() ; pit != sortedBottom.rend(); ++pit ) { for (unsigned int r=0; r < Size.size(); r++){ if((*pit==Bottom.at(r))&&(sortedLeft.at(q)==Left.at(r))){ compBkcode.push_back(Size.at(r));
                } } } }
                push_variant(compBkcode);
                
                if (bkCodes.empty()) { continue;
                }

                stringstream ss;
                int wordsize;
                vector<string> bkrowstring;
                if ((s[1] > s[2] )||(s[1] == s[2])) {
                    wordsize = ceil(log10(s[1]));
                    if (ceil(log10(s[1]))== log10(s[1])) wordsize++;
                } else {
                    wordsize = ceil(log10(s[2]));
                    if (ceil(log10(s[2]))== log10(s[2])) wordsize++;
                }

                unsigned int l = Size.size()+3;
                for (unsigned int p = 0; p < bkCodes.size() ; p++) {
                    for (unsigned int q = 0; q < l ; q++) {
                        ss << setw(wordsize) << setfill('0')<<bkCodes[p][q];
                    }
                    bkrowstring.push_back(ss.str());
                    ss.str("");
                    ss.clear();
                }
                std::vector<std::string>::iterator result = std::max_element(bkrowstring.begin(), bkrowstring.end());
                int qq = std::distance(bkrowstring.begin(), result) ;
                bkrowstring.clear();
                
                std::ostringstream bk;
                for (unsigned int j=0; j < Size.size()+3; j++){
                    bk<<bkCodes[qq][j]<<" ";
                }
                bk<<endl;
                
                string final_code = bk.str();
                bool string_has_zero = (final_code.find(" 0 ") != string::npos) || (final_code.find(" 0\n") != string::npos);

                if (has_zero_edges_flag || string_has_zero) {
                    std::vector<long long> filtered_elements;
                    long long d_width = bkCodes[qq][1];
                    long long d_height = bkCodes[qq][2];
                    
                    for(size_t k = 3; k < bkCodes[qq].size(); ++k) {
                        if (bkCodes[qq][k] > 0) {
                          filtered_elements.push_back(bkCodes[qq][k]);
                        }
                    }
                    
                    if (filtered_elements.empty()) { continue;
                    }
                    std::ostringstream dbk;
                    dbk << filtered_elements.size() << " " << d_width << " " << d_height;
                    for (size_t k = 0; k < filtered_elements.size(); ++k) {
                        dbk << " " << filtered_elements[k];
                    }
                    dbk << endl;
                    
                    degenerate_codes.emplace(dbk.str(), current_graph_hash);
                    
                } else {
                    if ((!is_compound) && do_simples && is_perfect && do_perfects && is_square && do_squares) {
                        spss.emplace(final_code, current_graph_hash);
                    }
                    if ((!is_compound) && do_simples && is_perfect && do_perfects && (!is_square) && do_rectangles) {
                        spsr.emplace(final_code, current_graph_hash);
                    }
                    if ((!is_compound) && do_simples && (!is_perfect) && do_imperfects && is_square && do_squares) {
                        siss.emplace(final_code, current_graph_hash);
                    }
                    if ((!is_compound) && do_simples && (!is_perfect) && do_imperfects && (!is_square) && do_rectangles) {
                        sisr.emplace(final_code, current_graph_hash);
                    }
                    if (is_compound && do_compounds && is_perfect && do_perfects && is_square && do_squares) {
                        cpss.emplace(final_code, current_graph_hash);
                    }
                    if (is_compound && do_compounds && is_perfect && do_perfects && (!is_square) && do_rectangles) {
                        cpsr.emplace(final_code, current_graph_hash);
                    }
                    if (is_compound && do_compounds && (!is_perfect) && do_imperfects && is_square && do_squares) {
                        ciss.emplace(final_code, current_graph_hash);
                    }
                    if (is_compound && do_compounds && (!is_perfect) && do_imperfects && (!is_square) && do_rectangles) {
                        cisr.emplace(final_code, current_graph_hash);
                    }
                }
                
                end_time = std::chrono::high_resolution_clock::now();
                time_check = end_time - start_time;
            } 
        } 
    } 
    
    duration_total = ( std::clock() - start_total ) / (double) CLOCKS_PER_SEC;
    std::cout<<"processing took "<< duration_total <<" seconds."<<'\n';
    return 0;
}
