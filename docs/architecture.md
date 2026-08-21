# EventFlow API Platform Architecture

See the system design portfolio for the visual architecture. This repository contains the corresponding service implementation.

## Production evolution

The local version keeps infrastructure compact for reproducibility. The service boundaries are designed to support separate persistence, queueing, worker, model serving, and observability components as traffic or dataset scale increases.
