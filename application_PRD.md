# Product Requirements Document: Decware Order Tracker

## Document Information
- **Document Title:** Decware Order Tracker - Product Requirements Document
- **Version:** 1.0
- **Date:** April 1, 2025
- **Status:** Draft

## Table of Contents
1. [Introduction](#introduction)
2. [Product Overview](#product-overview)
3. [User Requirements](#user-requirements)
4. [Functional Requirements](#functional-requirements)
5. [Non-Functional Requirements](#non-functional-requirements)
6. [Technical Specifications](#technical-specifications)
7. [Data Requirements](#data-requirements)
8. [User Interface Requirements](#user-interface-requirements)
9. [Implementation Timeline](#implementation-timeline)
10. [Appendices](#appendices)

## Introduction

### Purpose
This Product Requirements Document (PRD) outlines the requirements and specifications for the Decware Order Tracker application. The application will automatically download order data from the Decware website, store it in a database, and provide a user-friendly interface for customers to track their orders and view estimated completion times.

### Scope
The Decware Order Tracker will be a web-based application that automates the process of retrieving order information, tracking status changes, and calculating estimated completion times. It will provide a search interface for users to find their orders and view detailed information about order status and progress.

### Intended Audience
This document is intended for:
- Development team responsible for implementing the application
- Project managers overseeing the development process
- Stakeholders at Decware who will use or maintain the application
- Quality assurance team responsible for testing the application

### Definitions and Acronyms
- **CSV**: Comma-Separated Values, a file format used for the order data
- **API**: Application Programming Interface
- **UI**: User Interface
- **PRD**: Product Requirements Document

## Product Overview

### Product Perspective
The Decware Order Tracker is a standalone web application that will interact with the Decware website to retrieve order data. It will provide a more user-friendly and feature-rich interface for customers to track their orders compared to the current system.

### Product Features
1. Automated daily download of order data from the Decware website
2. Storage of order data in a relational database
3. Tracking of order status changes over time
4. Calculation of estimated completion times based on historical data
5. Search functionality for users to find their orders
6. Detailed order view with status history and estimated completion time
7. Cookie-based storage for saving selected orders for future reference

### User Classes and Characteristics
1. **End Users (Customers)**: Individuals who have placed orders with Decware and want to track their status
2. **Administrators**: Staff who will manage and maintain the application
3. **System Processes**: Automated processes that will download and process order data

### Operating Environment
The application will operate in a web environment and will be accessible through standard web browsers. The backend will run on a server with internet access to download data from the Decware website.

### Design and Implementation Constraints
1. The application must use PostgreSQL for the database
2. The frontend must be implemented using React with Material Design
3. The backend must be implemented using Python/Django
4. The application must be able to run on standard web hosting environments

### Assumptions and Dependencies
1. The Decware website will continue to provide order data in CSV format at the specified URL
2. The structure of the CSV file will remain consistent
3. The application will have permission to access the Decware website and download the CSV file
4. The server hosting the application will have internet access

## User Requirements

### User Stories
1. As a customer, I want to search for my order by my name and model number so that I can quickly find my specific order.
2. As a customer, I want to view detailed information about my order so that I can understand its current status.
3. As a customer, I want to see an estimated completion time for my order so that I can plan accordingly.
4. As a customer, I want to save my order for future reference so that I don't have to search for it again.
5. As a customer, I want to see the history of status changes for my order so that I can understand its progression.
6. As an administrator, I want the system to automatically download order data daily so that the information is always up-to-date.
7. As an administrator, I want the system to track status changes so that we can analyze order progression.
8. As an administrator, I want the system to calculate average completion times so that we can provide accurate estimates to customers.

### Use Cases
1. **Search for Order**
   - Actor: Customer
   - Description: Customer searches for their order by name and model
   - Preconditions: Customer has placed an order with Decware
   - Flow:
     1. Customer enters their name in the search field
     2. Customer optionally enters the model number
     3. System displays matching orders
   - Postconditions: Customer sees a list of matching orders

2. **View Order Details**
   - Actor: Customer
   - Description: Customer views detailed information about their order
   - Preconditions: Customer has found their order in the search results
   - Flow:
     1. Customer clicks on an order in the search results
     2. System displays detailed information about the order
   - Postconditions: Customer sees detailed order information

3. **Save Order for Future Reference**
   - Actor: Customer
   - Description: Customer saves an order for future reference
   - Preconditions: Customer is viewing order details
   - Flow:
     1. Customer clicks the "Save" button
     2. System saves the order in a browser cookie
   - Postconditions: Order is saved in the customer's browser

4. **Download Order Data**
   - Actor: System
   - Description: System downloads order data from the Decware website
   - Preconditions: System has internet access
   - Flow:
     1. System connects to the Decware website at the specified URL
     2. System downloads the CSV file
     3. System processes the CSV data
     4. System updates the database with new information
   - Postconditions: Database contains up-to-date order information

## Functional Requirements

### Data Acquisition
1. The system shall download a CSV file from https://orders.decware.com/list_view.php daily at midnight.
2. The system shall parse the CSV file and extract the following fields:
   - Date-Time
   - For (Customer Name)
   - From (Origin)
   - Qty (Quantity)
   - MODEL
   - Base
   - VOLTS
   - Options
   - Status
3. The system shall handle errors during the download and parsing process, including:
   - Network connectivity issues
   - Invalid CSV format
   - Missing or malformed data
4. The system shall log all download and parsing activities for monitoring and troubleshooting.

### Data Storage
1. The system shall store order data in a PostgreSQL database.
2. The system shall create a new record for each order if no matching record exists.
3. The system shall create a new record if an existing order's status has changed.
4. The system shall not create a duplicate record if all fields are identical to an existing record.
5. The system shall track the following additional fields for each record:
   - time_created: When the record was first created in the database
   - time_updated: When the record was last updated

### Order Tracking
1. The system shall track status changes for each order over time.
2. The system shall record the previous status, new status, and timestamp for each status change.
3. The system shall support the following status values:
   - "Passed Quality Control - Awaiting Payment"
   - "New"
   - "Quality Control"
   - "Completed waiting for wood base"
   - "Passed Quality Control"
   - "Testing"
   - "On Bench"
   - "Parts Pulled"
4. The system shall calculate metrics about the average time spent in each status.

### Order Search
1. The system shall provide a search interface for users to find orders.
2. The system shall allow users to search by customer name ("For" field).
3. The system shall allow users to search by model number ("MODEL" field).
4. The system shall display search results in a paginated table.
5. The system shall allow users to click on a search result to view detailed order information.

### Order Details
1. The system shall display detailed information about an order, including:
   - Customer information (name, origin)
   - Product information (model, base, volts, quantity, options)
   - Current status
   - Status history
   - Estimated completion time
2. The system shall allow users to save an order for future reference using browser cookies.
3. The system shall display a timeline of status changes for the order.

### Completion Time Estimation
1. The system shall calculate estimated completion times for orders based on historical data.
2. The system shall track the average time spent in each status.
3. The system shall estimate the remaining time for an order based on its current status and the average time for remaining statuses.
4. The system shall provide a confidence level for each estimate (high or low).
5. The system shall display the estimated days remaining and estimated completion date.

## Non-Functional Requirements

### Performance
1. The system shall load search results within 2 seconds.
2. The system shall load order details within 1 second.
3. The system shall process the daily CSV download within 5 minutes.
4. The system shall support at least 100 concurrent users.

### Reliability
1. The system shall be available 99.9% of the time.
2. The system shall retry failed CSV downloads up to 3 times.
3. The system shall maintain data integrity during database operations.
4. The system shall log all errors and exceptions for troubleshooting.

### Security
1. The system shall not require user authentication for basic order tracking.
2. The system shall not store sensitive customer information beyond what is provided in the CSV file.
3. The system shall use secure connections for all data transfers.

### Usability
1. The system shall use Material Design for a consistent and user-friendly interface.
2. The system shall be responsive and work on desktop and mobile devices.
3. The system shall provide clear error messages when issues occur.
4. The system shall provide helpful instructions for using the search functionality.

### Maintainability
1. The system shall be well-documented with code comments and external documentation.
2. The system shall use a modular architecture for easy maintenance and updates.
3. The system shall include comprehensive tests for all components.
4. The system shall log all activities for monitoring and troubleshooting.

### Compatibility
1. The system shall work with modern web browsers, including Chrome, Firefox, Safari, and Edge.
2. The system shall be responsive and work on desktop and mobile devices.

## Technical Specifications

### Architecture
The application will follow a three-tier architecture:
1. **Presentation Layer**: React frontend with Material Design
2. **Application Layer**: Django backend with RESTful API
3. **Data Layer**: PostgreSQL database

### Database Schema
The database will include the following tables:
1. **OrderRecord**:
   - id (Primary Key)
   - order_datetime (Timestamp)
   - customer_name (String)
   - origin (String)
   - quantity (Integer)
   - model (String)
   - base (String)
   - volts (String)
   - options (Text)
   - status (String)
   - time_created (Timestamp)
   - time_updated (Timestamp)

2. **StatusHistory**:
   - id (Primary Key)
   - order_record_id (Foreign Key)
   - previous_status (String)
   - new_status (String)
   - change_datetime (Timestamp)

3. **StatusMetrics**:
   - id (Primary Key)
   - from_status (String)
   - to_status (String)
   - avg_days_in_status (Float)
   - sample_size (Integer)
   - last_calculated (Timestamp)

### API Endpoints
The backend will provide the following API endpoints:
1. **GET /api/orders/search**: Search for orders by customer name and model
2. **GET /api/orders/{id}**: Get detailed information about a specific order
3. **GET /api/status/metrics**: Get metrics about average time spent in each status
4. **GET /api/status/progression**: Get the expected status progression and current average times

### Frontend Components
The frontend will include the following components:
1. **App**: Main application component
2. **Header**: Application header with navigation
3. **Footer**: Application footer with information
4. **SearchPage**: Page for searching orders
5. **OrderDetailsPage**: Page for viewing order details

### Technologies
The application will use the following technologies:
1. **Frontend**:
   - React
   - Material UI
   - Axios for API requests
   - React Router for navigation
   - Local Storage/Cookies for saving orders

2. **Backend**:
   - Python
   - Django
   - Django REST Framework
   - PostgreSQL
   - Requests for downloading CSV

3. **Deployment**:
   - Gunicorn for serving the Django application
   - Nginx for serving static files and proxying requests
   - Cron for scheduling the daily CSV download

## Data Requirements

### Data Sources
The primary data source for the application is the CSV file downloaded from https://orders.decware.com/list_view.php. This file contains information about orders, including customer information, product details, and current status.

### Data Entities
The application will track the following data entities:
1. **Order**: Represents a customer order with all associated information
2. **Status Change**: Represents a change in order status over time
3. **Status Metric**: Represents metrics about average time spent in each status

### Data Validation
The application will validate the following aspects of the data:
1. Required fields are present in the CSV file
2. Data types are correct (e.g., dates are valid dates, quantities are numbers)
3. Status values are one of the expected values
4. Timestamps are valid and in the expected format

### Data Retention
The application will retain all order data and status history indefinitely for historical analysis and accurate completion time estimation.

## User Interface Requirements

### General UI Requirements
1. The UI shall follow Material Design guidelines for a consistent and user-friendly experience.
2. The UI shall be responsive and work on desktop and mobile devices.
3. The UI shall use a clean, professional color scheme.
4. The UI shall provide clear feedback for user actions.

### Search Interface
1. The search interface shall include fields for customer name and model.
2. The search interface shall include a search button that is disabled until at least one search field is filled.
3. The search interface shall display a loading indicator during search operations.
4. The search interface shall display search results in a paginated table.
5. The search interface shall display an appropriate message when no results are found.

### Order Details Interface
1. The order details interface shall display customer information, product details, and current status.
2. The order details interface shall display a timeline of status changes.
3. The order details interface shall display estimated completion time with confidence level.
4. The order details interface shall include a button to save the order for future reference.
5. The order details interface shall include a button to return to the search results.

### Mockups
(Note: In a complete PRD, this section would include wireframes or mockups of the user interface. For this document, we'll omit the actual mockups.)

## Implementation Timeline

### Phase 1: Planning and Setup (Weeks 1-2)
1. Finalize requirements and specifications
2. Set up development environment
3. Create project structure
4. Design database schema

### Phase 2: Backend Development (Weeks 3-5)
1. Implement database models
2. Develop CSV download and parsing functionality
3. Implement data storage and comparison logic
4. Create API endpoints for order search and details
5. Implement status tracking and time estimation algorithms

### Phase 3: Frontend Development (Weeks 6-8)
1. Set up React project with Material UI
2. Implement search interface
3. Develop order details view
4. Implement status timeline visualization
5. Add cookie-based storage for saved orders

### Phase 4: Testing and Refinement (Weeks 9-10)
1. Develop comprehensive test suite
2. Perform unit testing of all components
3. Conduct integration testing
4. Perform user acceptance testing
5. Fix bugs and refine functionality based on feedback

### Phase 5: Deployment and Documentation (Weeks 11-12)
1. Set up production environment
2. Deploy application
3. Create user documentation
4. Create technical documentation
5. Train administrators on system maintenance

## Appendices

### Appendix A: Glossary
- **CSV**: Comma-Separated Values, a file format used for the order data
- **API**: Application Programming Interface
- **UI**: User Interface
- **PRD**: Product Requirements Document
- **React**: A JavaScript library for building user interfaces
- **Django**: A Python web framework
- **PostgreSQL**: An open-source relational database management system
- **Material Design**: A design language developed by Google

### Appendix B: References
1. Decware website: https://orders.decware.com
2. PostgreSQL documentation: https://www.postgresql.org/docs/
3. Django documentation: https://docs.djangoproject.com/
4. React documentation: https://reactjs.org/docs/
5. Material UI documentation: https://mui.com/

### Appendix C: Approval
This Product Requirements Document requires approval from the following stakeholders:
- Project Manager
- Lead Developer
- Quality Assurance Lead
- Client Representative

---

Document End
