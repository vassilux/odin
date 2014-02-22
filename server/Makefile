REPORTER = dot

test:
	@NODE_ENV=test
	@./node_modules/.bin/mocha -u tdd --reporter $(REPORTER)
  
test-w:
	@NODE_ENV=test 
	@./node_modules/.bin/mocha -u tdd --reporter $(REPORTER)

.PHONY: test test-w