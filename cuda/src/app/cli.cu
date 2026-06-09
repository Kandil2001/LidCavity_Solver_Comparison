static RunConfig parse_args(int argc, char** argv) {
    RunConfig c;
    for (int i=1;i<argc;++i) {
        std::string a = argv[i];
        auto need=[&](const char* name){ if (i+1>=argc) { std::cerr << "Missing value for " << name << "\n"; std::exit(2);} return std::string(argv[++i]); };
        if (a=="--N") c.N = std::stoi(need("--N"));
        else if (a=="--Re") c.Re = std::stoi(need("--Re"));
        else if (a=="--scheme") c.scheme = need("--scheme");
        else if (a=="--pressure") c.pressure = need("--pressure");
        else if (a=="--maxIter") c.maxIter = std::stoi(need("--maxIter"));
        else if (a=="--poisson-maxIter") c.poissonIter = std::stoi(need("--poisson-maxIter"));
        else if (a=="--block-size") c.blockSize = std::stoi(need("--block-size"));
        else if (a=="--no-fields") c.save_fields=false;
        else if (a=="--mode") { c.mode = need("--mode"); if (c.mode=="smoke") { c.N=16; c.Re=100; c.maxIter=20; c.poissonIter=50; c.scheme="upwind"; } }
    }
    return c;
}

