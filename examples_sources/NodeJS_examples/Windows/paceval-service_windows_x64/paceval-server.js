const express = require('express');
const app = express();
const ffi = require('ffi-napi');
const ref = require('ref-napi');

const platform = process.platform;
const architecture = process.arch;
var numberOfActiveComputations = 0;
var pacevalComputations_arr = [];

app.use(express.json());
app.use(express.urlencoded({ extended: true }));


function pacevalLibraryName()
{
    var pacevalLibrary_str = null;

    if (((platform === 'win32') || (platform === 'win64')) && (architecture === 'x64'))
    {
        pacevalLibrary_str = 'paceval_win64i';
    }
    else if ((platform === 'linux') && (architecture === 'x64'))
    {
        pacevalLibrary_str = './libpaceval_linux_sharedLIB.so';
    }
    else if ((platform === 'linux') && (architecture === 'arm64'))
    {
        pacevalLibrary_str = './libpacevalARM64_sharedLIB.so';
    }
    else
    {
        throw new Error('unsupported platform and architecture for pacevalLibrary : '
                        + platform + ' ' + architecture + '-please, contact us via info@paceval.com')
    }

    return pacevalLibrary_str;
}

function findComputationPos(arg)
{
    var numberOfComputations = pacevalComputations_arr.length;

    for (var iCount = 0; iCount < numberOfComputations; iCount++)
    {
        if (pacevalComputations_arr[iCount][0] == arg)
        {
            return iCount;
        }
    }

    return -1;
}

function deleteComputationTimer(arg)
{
    var paceval_ffi = ffi.Library(pacevalLibraryName(),
    {
        'pacevalLibrary_DeleteComputation': [ 'bool', [ 'pointer' ] ],
        'pacevalLibrary_Free': [ 'bool', [ ] ]
    });

    var position = findComputationPos(arg);

    if (position >= 0)
    {
        var success = paceval_ffi.pacevalLibrary_DeleteComputation(pacevalComputations_arr[position][1]);

        if (success == true)
        {
            console.log(`deleted paceval. computation handle_pacevalComputation: ${arg}`);

            pacevalComputations_arr.splice(position, 1);

            numberOfActiveComputations--;
            if (numberOfActiveComputations == 0)
            {
                success = paceval_ffi.pacevalLibrary_Free();
            }
        }
    }
}

function handleGETandPOST(req, res)
{
    var handle_pacevalComputation_str = "";

    if (req.query.call != null) //GET
    {
        if (req.query.call != "paceval")
        {
            res.status(500).json({ error: 'missing parameters' });
            return;
        }
        handle_pacevalComputation_str = req.query.handle_pacevalComputation;
    }
    else if (req.body.call != null) //POST
    {
        if (req.body.call != "paceval")
        {
            res.status(500).json({ error: 'missing parameters' });
            return;
        }
        handle_pacevalComputation_str = req.body.handle_pacevalComputation;
    }
    if ((req.query.call == null) && (req.body.call == null))
    {
            res.status(500).json({ error: 'missing parameters' });
            return;
    }

    var handle_pacevalComputation = null;
    var existingComputation = false;
    var isError = false;
    var numberOfVariables = 0;
    var function10chars = '';
    var functionLength = 0;
    var interval = false;

    if (handle_pacevalComputation_str != null)
    {
        var position = findComputationPos(handle_pacevalComputation_str);
        if (position >= 0)
        {
            console.log(`reuse paceval. computation handle_pacevalComputation: ${handle_pacevalComputation_str}`);

            clearTimeout(pacevalComputations_arr[position][2]);
            handle_pacevalComputation = pacevalComputations_arr[position][1];
            numberOfVariables = pacevalComputations_arr[position][3];
            function10chars = pacevalComputations_arr[position][4];
            functionLength = pacevalComputations_arr[position][5];
            existingComputation = true;
        }
        else
        {
            res.status(500).json({ error: 'handle_pacevalComputation does not exist' });
            return;
        }
    }

    if (existingComputation == false)
    {
        if (req.query.call != null) //GET
        {
            var function_str = req.query.functionString;
            numberOfVariables = parseInt(req.query.numberOfVariables);
            var variables_str = req.query.variables.replace(/;/g, ' ');
            values_ar = JSON.parse("[" + req.query.values.replace(/;/g, ',') + "]");
            var interval_str = req.query.interval;
        }
        else if (req.body.call != null) //POST
        {
            var function_str = req.body.functionString;
            numberOfVariables = parseInt(req.body.numberOfVariables);
            var variables_str = req.body.variables.replace(/;/g, ' ');
            values_ar = JSON.parse("[" + req.body.values.replace(/;/g, ',') + "]");
            var interval_str = req.body.interval;
        }

        if ((interval_str == "yes") || (interval_str == "true"))
            interval = true;
    }
    else
    {
        if (req.query.call != null) //GET
            values_ar = JSON.parse("[" + req.query.values.replace(/;/g, ',') + "]");
        else if (req.body.call != null) //POST
            values_ar = JSON.parse("[" + req.body.values.replace(/;/g, ',') + "]");
    }

    var ArrayType = require('ref-array-napi');
    var now = require("performance-now");

    console.log(`handle new data - timestamp: ${new Date().toISOString()}`);

    var pacevalLibrary_str = pacevalLibraryName();

    var double = ref.types.double;
    var int = ref.types.int;
    var doubleArray = ArrayType('double');
    var doublePtr = ref.refType('double');
    var intPtr = ref.refType('int');

    var paceval_ffi = ffi.Library(pacevalLibrary_str,
    {
        'pacevalLibrary_Initialize': [ 'bool', [ 'string' ] ],
        'pacevalLibrary_CreateComputation': [ 'pointer', [ 'string', 'uint32', 'string', 'int', 'pointer' ] ],
        'pacevalLibrary_GetIsError': [ 'bool', [ 'pointer' ] ],
        'pacevalLibrary_dmathv': [ 'double', [ 'pointer', intPtr , 'string', 'uint32', 'string', doubleArray ] ],

        'pacevalLibrary_CreateErrorInformationText': [ 'int', [ 'pointer', 'char*', 'char*' ] ],
        'pacevalLibrary_dGetComputationResult': [ 'double', [ 'pointer', doubleArray , doublePtr , doublePtr ] ],
        'pacevalLibrary_dConvertFloatToString': [ 'int', [ 'pointer', double ] ],
        'pacevalLibrary_DeleteComputation': [ 'bool', [ 'pointer' ] ]
    });

    if (existingComputation == false)
    {
        if (numberOfActiveComputations == 0)
        {
            var success = paceval_ffi.pacevalLibrary_Initialize(null);
        }
    }

    valuesVariablesArray = new doubleArray(numberOfVariables);
    for (iCount = 0; iCount < numberOfVariables; iCount++)
    {
        valuesVariablesArray[iCount] = values_ar[iCount];
    }

    var trustedMinResult = ref.alloc('double');
    var trustedMaxResult = ref.alloc('double');
    var timeCreate = 0;
    var result_str = Buffer.alloc(25, 0, "ascii");
    var trustedMinResult_str = Buffer.alloc(25, 0, "ascii");
    var trustedMaxResult_str = Buffer.alloc(25, 0, "ascii");

    if (existingComputation == false)
    {
        timeCreate = now();
        var handle_pacevalComputation = paceval_ffi.pacevalLibrary_CreateComputation(function_str,
                                        numberOfVariables, variables_str, interval, null);
        timeCreate = (now() - timeCreate) / 1000;
        numberOfActiveComputations++;
        isError = paceval_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
        
        console.log(`created new paceval. computation handle_pacevalComputation: ${handle_pacevalComputation.address()}`);
    }

    var handle_pacevalComputation_addr = handle_pacevalComputation.address();

    if (isError == false)
    {
        var timeCalculate = now(true);
        var result = paceval_ffi.pacevalLibrary_dGetComputationResult(handle_pacevalComputation,
                     valuesVariablesArray, trustedMinResult, trustedMaxResult);
        timeCalculate = (now() - timeCalculate) / 1000;
      
        isError = paceval_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
        var success = paceval_ffi.pacevalLibrary_dConvertFloatToString(result_str, result);

        if (interval == true)
        {
            success = paceval_ffi.pacevalLibrary_dConvertFloatToString(trustedMinResult_str, trustedMinResult.deref());
            success = paceval_ffi.pacevalLibrary_dConvertFloatToString(trustedMaxResult_str, trustedMaxResult.deref());
        }
    }
    else
        var timeCalculate = 0;

    if (existingComputation == false)
    {
        functionLength = function_str.length;
        function10chars = function_str.substring(0, 10);
        if (functionLength > 10)
        {
            function10chars = function10chars + "(...)";
        }
    }

    var maxLengthStr = paceval_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation, null, null);
    var errorMessage_str = Buffer.alloc(maxLengthStr, 0, "ascii");
    var errorDetails_str = Buffer.alloc(maxLengthStr, 0, "ascii");
    maxLengthStr = paceval_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation,
                   errorMessage_str, errorDetails_str);

    var errorType = ref.alloc('int');
    var threadUsages = paceval_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_NumberThreadUsages', 0, "", null);
    var cacheHitsACC = paceval_ffi.pacevalLibrary_dmathv(null, errorType, "paceval_NumberCacheHitsACC", 0, "", null);
    var numberOfCores = paceval_ffi.pacevalLibrary_dmathv(null, errorType, "paceval_NumberOfCores", 0, "", null);
    var versionNumber = paceval_ffi.pacevalLibrary_dmathv(null, errorType, "paceval_VersionNumber", 0, "", null);

    var return_arr =
    {
        "result": result_str.toString().replace(/\0/g, ''),
        "interval-min-result": trustedMinResult_str.toString().replace(/\0/g, ''),
        "interval-max-result": trustedMaxResult_str.toString().replace(/\0/g, ''),
        "function-10chars": function10chars,
        "function-length": functionLength,
        "error-type": errorDetails_str.toString().replace(/\0/g, ''),
        "number-of-thread-usages": threadUsages,
        "number-of-cache-hits": cacheHitsACC,
        "number-of-cores": numberOfCores,
        "number-of-active-computations": numberOfActiveComputations,
        "time-create": timeCreate.toFixed(6) + "s",
        "time-calculate": timeCalculate.toFixed(6) + "s",
        "error-message": errorMessage_str.toString().replace(/\0/g, ''),
        "handle_pacevalComputation": handle_pacevalComputation_addr,
        "version-number": versionNumber
    };

    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(return_arr));

    const timeoutDeleteComputation = setTimeout(deleteComputationTimer, 3600000, handle_pacevalComputation_addr); //1 hour

    if (existingComputation == false)
    {
        pacevalComputations_arr.push([ handle_pacevalComputation_addr, handle_pacevalComputation, timeoutDeleteComputation,
                                       numberOfVariables, function10chars, functionLength ]);

        console.log(`1 hour deletion timer created for paceval. computation handle_pacevalComputation: ${handle_pacevalComputation.address()}`);
    }
    else
    {
        pacevalComputations_arr[position][2] = timeoutDeleteComputation;
   
        console.log(`deletion timer prolonged by 1 hour for paceval. computation handle_pacevalComputation: ${handle_pacevalComputation.address()}`);
    }
};

app.get('/', (req, res) =>
{
    handleGETandPOST(req, res);
});

app.post('/', (req, res) =>
{
    handleGETandPOST(req, res);
});

// Listen to the App Engine-specified port, or 8080 otherwise
const PORT = process.env.PORT || 8080;
app.listen(PORT, () =>
{
    console.log(`paceval. server listening on port ${PORT}...`);
});

