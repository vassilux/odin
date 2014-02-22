var request = require('superagent'); 
var expect = require('expect.js');
var sysinfo = require('../lib/sysinfo.js')

describe('sysinfo test suite ', function(){
		it('I must take the system informations ', function(done){
			sysinfo.get('localhost', 3003, function(data){
				console.log("data : " + data);
				var packet = JSON.parse(data);
				done();
			});
		
	});
});