# Agents Module

## Purpose

This folder contains the base framework for all agents used in the project.

## BaseAgent

BaseAgent is the parent class for every agent.

Every new agent should inherit from this class.

## SupervisedAgent

A simple implementation of BaseAgent.

Currently it only prints a message and returns the updated state.

## AgentState

Stores information shared between agents.

Current fields:

- user_query
- current_agent
- status

Future agents can use this state object to exchange information.