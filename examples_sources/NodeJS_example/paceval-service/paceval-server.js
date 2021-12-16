const express = require('express');
const app = express();
const ffi = require('ffi-napi');
const ref = require('ref-napi');

const platform = process.platform;
const architecture = process.arch;
var numberOfActiveComputations = 0;
var pacevalComputations_arr = []; 

function pacevalLibraryName() 
{
    var pacevalLibrary_str = null;

    if (((platform === 'win32') || (platform === 'win64')) && (architecture === 'x64')) 
    {
        pacevalLibrary_str = 'paceval_win64i';
    } 
    else if ((platform === 'linux') && (architecture === 'x64')) 
    {
        pacevalLibrary_str = 'libpaceval_linux_sharedLIB';
    } 
    else if ((platform === 'linux') && (architecture === 'arm64')) 
    {
        pacevalLibrary_str = 'libpacevalARM64_sharedLIB';
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
    console.log(`time start delete computation => ${Date.now()}`);
    console.log(`computation was => ${arg}`);

    var paceval_ffi = ffi.Library(pacevalLibraryName(), {
      'pacevalLibrary_DeleteComputation': [ 'bool', [ 'pointer' ] ],
      'pacevalLibrary_Free': [ 'bool', [ ] ]
    });

    var position = findComputationPos(arg);

    if (position >= 0)
    { 
      var success = paceval_ffi.pacevalLibrary_DeleteComputation(pacevalComputations_arr[position][1]);
      console.log(`pacevalLibrary_DeleteComputation(...) => ${success}`);

      if (success == true)
      {
        pacevalComputations_arr[position][0] = null; //handle_pacevalComputation_addr
        pacevalComputations_arr[position][1] = null; //handle_pacevalComputation
        pacevalComputations_arr[position][2] = null; //timeoutDeleteComputation
        pacevalComputations_arr[position][3] = null;

        console.log(`array length was => ${pacevalComputations_arr.length}`);
        pacevalComputations_arr.splice(position, 1);
        console.log(`array length was => ${pacevalComputations_arr.length}`);

        numberOfActiveComputations--;
        if (numberOfActiveComputations == 0)
        {
          success = paceval_ffi.pacevalLibrary_Free();
          console.log(`pacevalLibrary_Free() => ${success}`);
        }
      }
    }
}

function handleGETandPOST(req, res) 
{
   var call_str = req.query.call;
   if (call_str != "paceval")
   {
     res.status(500).json({ error: 'missing parameters' });
     return;
   }

    var handle_pacevalComputation_str = req.query.handle_pacevalComputation;
    var handle_pacevalComputation = null;
    var existingComputation = false;
    var isError = false;
    var numberOfVariables = 0;
    var function10chars = '';
    var functionLength = 0;

    if (handle_pacevalComputation_str != null)
    {
      console.log(`handle_pacevalComputation => ${handle_pacevalComputation_str}`);
      var position = findComputationPos(handle_pacevalComputation_str);
      if (position >= 0)
      {
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

      console.log(`findComputationPos(...) => ${position}`);
    }

    if (existingComputation == false)
    {
      var function_str = req.query.functionString;
      console.log(`function_str => ${function_str}`);
      numberOfVariables = parseInt(req.query.numberOfVariables);
      console.log(`numberOfVariables => ${numberOfVariables}`);
      var variables_str = req.query.variables.replace(';', ' ');
      console.log(`variables_str => ${variables_str}`);
      values_ar = JSON.parse("[" + req.query.values.replace(';', ',') + "]");
      console.log(`values_ar => ${values_ar}`);
      var interval_str = req.query.interval;
      console.log(`interval_str => ${interval_str}`);

      if ((interval_str == "yes") || (interval_str == "true"))
        var interval = true;
    }
    else
    {
      values_ar = JSON.parse("[" + req.query.values.replace(';', ',') + "]");
      console.log(`values_ar => ${values_ar}`);
    }

    var ArrayType = require('ref-array-napi');
    var now = require("performance-now");

    console.log(`time start get => ${Date.now()}`);
    var pacevalLibrary_str = pacevalLibraryName();

    var double = ref.types.double;
    var int = ref.types.int;
    var doubleArray = ArrayType('double');
    var doublePtr = ref.refType('double');
    var intPtr = ref.refType('int');

    var paceval_ffi = ffi.Library(pacevalLibrary_str, {
      'pacevalLibrary_Initialize': [ 'bool', [ 'string' ] ],
      'pacevalLibrary_CreateComputation': [ 'pointer', [ 'string', 'uint32', 'string', 'int', 'pointer' ] ],
      'pacevalLibrary_GetIsError': [ 'bool', [ 'pointer' ] ],
      'pacevalLibrary_dmathv': [ 'double', [ 'pointer', intPtr , 'string', 'uint32', 'string', doubleArray ] ], 
      'pacevalLibrary_CreateErrorInformationText': [ 'int', [ 'pointer', 'char*', 'char*' ] ],
      'pacevalLibrary_dGetComputationResult': [ 'double', [ 'pointer', doubleArray , doublePtr , doublePtr ] ],
      'pacevalLibrary_DeleteComputation': [ 'bool', [ 'pointer' ] ]
    }); 

    if (existingComputation == false)
    {
      if (numberOfActiveComputations == 0)
      {
        var success = paceval_ffi.pacevalLibrary_Initialize(null);
        console.log(`pacevalLibrary_Initialize(...) => ${success}`);
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

    if (existingComputation == false)
    {
      timeCreate = now();
      var handle_pacevalComputation = paceval_ffi.pacevalLibrary_CreateComputation(function_str, 
        numberOfVariables, variables_str, interval, null);
      timeCreate = (now() - timeCreate) / 1000;
      numberOfActiveComputations++;
      isError = paceval_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
      console.log(`pacevalLibrary_CreateComputation(...) => ${handle_pacevalComputation_addr}`);
    }

    var handle_pacevalComputation_addr = handle_pacevalComputation.address();
    
    if (isError == false)
    {
      var timeCalculate = now(true);
      var result = paceval_ffi.pacevalLibrary_dGetComputationResult(handle_pacevalComputation, 
              valuesVariablesArray, trustedMinResult, trustedMaxResult);
      timeCalculate = (now() - timeCalculate) / 1000;
  
      isError = paceval_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
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
    console.log(`pacevalLibrary_CreateErrorInformationText(...) => ${maxLengthStr}`);
    var errorMessage_str = Buffer.alloc(maxLengthStr, 0, "ascii");
    var errorDetails_str = Buffer.alloc(maxLengthStr, 0, "ascii");
    maxLengthStr = paceval_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation, 
      errorMessage_str, errorDetails_str);
    
    var errorType = ref.alloc('int');
    var threadUsages = paceval_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_NumberThreadUsages', 0, "", null);
    var cacheHitsACC = paceval_ffi.pacevalLibrary_dmathv(null, errorType, "paceval_NumberCacheHitsACC", 0, "", null);
    var numberOfCores = paceval_ffi.pacevalLibrary_dmathv(null, errorType, "paceval_NumberOfCores", 0, "", null);

    var return_arr = 
    { 
      "result": result,  
      "interval-min-result": trustedMinResult.deref(),  
      "interval-max-result": trustedMaxResult.deref(), 
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
      "handle_pacevalComputation": handle_pacevalComputation_addr 
    }; 

    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(return_arr));

    const timeoutDeleteComputation = setTimeout(deleteComputationTimer, 3600000, handle_pacevalComputation_addr); //1 hour

    if (existingComputation == false)
    {
      pacevalComputations_arr.push([ handle_pacevalComputation_addr, handle_pacevalComputation, timeoutDeleteComputation, 
        numberOfVariables, function10chars, functionLength ]); 
    }
    else
      pacevalComputations_arr[position][2] = timeoutDeleteComputation;
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
app.listen(PORT, () => {
  console.log(`paceval. server listening on port ${PORT}...`);
});

