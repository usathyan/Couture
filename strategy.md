### **Phase 1: Project Initialization & Foundation**

This phase focuses on setting up the development environment, project structure, and essential tooling.

1.  **Version Control:** Initialize a Git repository to track all changes.
2.  **Project Structure:** Create a clean, organized directory structure for our code, documentation, and configuration.
3.  **Virtual Environment:** Use `uv` to create an isolated Python virtual environment, ensuring our dependencies don't conflict with other projects.
4.  **Initial Documentation:**
    *   **`README.md`:** Create a README file with a project overview, setup instructions, and usage guide.
    *   **`Architecture.md`:** Create a dedicated document to detail the technical architecture as we define it.
5.  **Automation with `Makefile`:** Create a `Makefile` with initial targets to streamline common tasks:
    *   `install`: To set up the environment and install dependencies.
    *   `lint`: To run code quality checks using `ruff` and `pyright`.
    *   `run`: To start the application locally.
    *   `test`: To execute the test suite.

---

### **Phase 2: Architecture & Backend Design**

In this phase, we will design the core of the backend system. This will be documented in `Architecture.md`. **Our primary goal is to build a version that works completely locally before deploying to the cloud.**

1.  **API:** We will use **FastAPI** to build a modern, high-performance RESTful API, run with `uvicorn` for local development.
2.  **Data Modeling:** We'll use **Pydantic** to define clear, type-safe data models for all business entities:
    *   `User` (with roles like `Manager`, `ProcurementStaff`)
    *   `Saree` (our core product)
    *   `ProcurementRecord`
    *   `Expense`
    *   `Sale`
    *   `Discount`
3.  **Database:** We'll use **Amazon DynamoDB**. For local development, we will use **DynamoDB Local**, which runs in a Docker container, allowing us to build and test without needing an AWS account.
4.  **File Storage:** For handling file uploads (e.g., proof of purchase), we will use a local directory during local development. This can be easily swapped with **Amazon S3** when we deploy to the cloud.
5.  **Data Interaction:** We'll leverage libraries like **`boto3`** (the AWS SDK) for communicating with DynamoDB Local. We can still use **`awswrangler`** and **`polars`** for any complex data reporting or analysis tasks.
6.  **Authentication:** Secure our API with **JWT (JSON Web Tokens)** for user authentication and role-based access control.
7.  **Containerization:** We will create a **`Dockerfile`** to package the Python application. This allows us to run tests in a consistent environment and is required for deployment to AWS Lambda later.

---

### **Phase 3: Local-First MVP Implementation (Iterative)**

We will build the core features of the application one module at a time, focusing entirely on the local environment first.

1.  **User Management & Auth:** Implement endpoints for user creation, login, and profile management.
2.  **Procurement Module:**
    *   Build the API endpoint for the procurement team to record new saree purchases.
    *   This will handle image uploads to a local folder and perform real-time currency conversion from INR to USD.
3.  **Product & Pricing Module:**
    *   Create endpoints for managers to view the inventory of sarees.
    *   Implement logic to set markups (either globally or per-saree) and automatically calculate the final selling price.
4.  **Expense & Sales Module:**
    *   Develop endpoints for submitting and approving expenses.
    *   Create endpoints to record sales and apply discounts.
5.  **Reporting (Basic):** Implement initial reporting endpoints to provide insights into sales, costs, and profits.

---

### **Phase 4: Cloud Deployment with AWS CDK (Post-Local MVP)**

Once the local MVP is fully functional and tested, we will deploy it to the cloud.

1.  **Infrastructure as Code:** We will use the **AWS Cloud Development Kit (CDK)** with Python to define our entire cloud infrastructure in code. This includes:
    *   **AWS Lambda** to run our containerized FastAPI application in a serverless environment.
    *   **Amazon API Gateway** to expose our API to the internet with a public URL, routing requests to our Lambda function.
    *   **Amazon DynamoDB** for our serverless NoSQL database.
    *   **Amazon S3** for file storage (e.g., proof of purchase images).
2.  **Deployment Automation:** We will add a `deploy` target to our `Makefile` to provide a simple, one-command deployment process.

---

### **Phase 5: Frontend Mobile App (Future)**

While this plan focuses on the backend, the API we build will be ready to support the Android and iOS applications. When we get to that stage, we can choose a cross-platform framework like **React Native** or **Flutter** to build both apps from a single codebase, which will communicate with our powerful Python backend.

This plan provides a clear roadmap for building a robust and scalable application that meets all the requirements you've outlined. We can start with Phase 1 whenever you're ready. 