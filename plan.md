## Objective

I would like to create an app (Android and IOS) to manage bookkeeping for a small business that sells mysore silk sarees. 

The entity (the main company that sells these sarees in the USA) sells it via a WhatsApp store. They list sarees wtih a US$. The company imports the sarees from Bangalore, India. The entity is managed by a set of partners. They all need personalized access to various aspcts of this booking process. Some of them will be submitting expenses themselves, review expenses, review costs, approve costs, approve resources etc. They are the managers of the comapany with specific roles. Provide suggestive roles and their responsbilities needed to manage this sort of business.

The mysore silk sarees are procured in Bangalore India, by a team of people employed for such purposes. They will use the app to scan the purchase the legally purchased product with proof, and the procurement cost in INR. A current transaction to US$ must be applied based on correct transaction rate as of that date.  The management team in the US, sets a global markup rate, or will have the ability to set a % markup per product.

There must be opitions to create and apply discounts.

Provide all typical bookkeeping functionality for capturing data, analyzing data, repirting, and other aspects of managing this process. If transfer pricing apply, provide a mechanism to capture that. 

## Technical aspects

I would like a  backend that can be deployed into AWS via CDK. Use Python stack, wth uv package management, Makefiles with targets for easy buiids, testing and deployment. This must be tested as a standalone docker container on local, but have cdk deployment for deploying to aws as ECS, with a public facing URL. This will follow standard python implementations, and be synced wtih git project. Provide a structured codebase, that contains modules for each section. Design an architecture based on best practices. I would like to use Makefiles, use uv package makagers, and one click install, test, run, deploy type targetrs in Makefiles. use ruff, pyrefly, and ty linters if possible, use pydantic, polars, awswrangler and other best performing libraries if needed. Keep the design simple and straightforwad. We can iterate with building more error handling and optimization iteratively. build MVPs. 

