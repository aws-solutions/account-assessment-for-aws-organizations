// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Stack } from 'aws-cdk-lib';
import { CfnResource, Aspects } from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { Construct } from 'constructs';
import { addCfnGuardSuppressions, CfnGuardSuppressResourceList } from "../lib/helpers/add-cfn-guard-suppression";

describe('CfnGuardSuppressResourceList', () => {
  let stack: Stack;

  beforeEach(() => {
    stack = new Stack();
  });

  test('adds suppressions to resource with matching type', () => {
    new TestResource(stack, 'TestResource');
    const suppressions = {
      'AWS::Test::Resource': ['TEST_RULE_1', 'TEST_RULE_2'],
    };

    Aspects.of(stack).add(new CfnGuardSuppressResourceList(suppressions));

    const template = Template.fromStack(stack);
    template.hasResource('AWS::Test::Resource', {
      Metadata: {
        guard: {
          SuppressedRules: ['TEST_RULE_1', 'TEST_RULE_2'],
        },
      },
    });
  });

  test('adds suppressions to resource with default child', () => {
    new ParentWithDefaultChild(stack, 'ParentConstruct');
    const suppressions = {
      'AWS::Test::ChildResource': ['CHILD_RULE'],
    };

    Aspects.of(stack).add(new CfnGuardSuppressResourceList(suppressions));

    const template = Template.fromStack(stack);
    template.hasResource('AWS::Test::ChildResource', {
      Metadata: {
        guard: {
          SuppressedRules: ['CHILD_RULE'],
        },
      },
    });
  });

  test('handles multiple suppressions for different resource types', () => {
    new TestResource(stack, 'TestResource1');
    new DifferentTestResource(stack, 'TestResource2');
    const suppressions = {
      'AWS::Test::Resource': ['RULE_1'],
      'AWS::Test::DifferentResource': ['RULE_2'],
    };

    Aspects.of(stack).add(new CfnGuardSuppressResourceList(suppressions));

    const template = Template.fromStack(stack);
    template.hasResource('AWS::Test::Resource', {
      Metadata: {
        guard: {
          SuppressedRules: ['RULE_1'],
        },
      },
    });
    template.hasResource('AWS::Test::DifferentResource', {
      Metadata: {
        guard: {
          SuppressedRules: ['RULE_2'],
        },
      },
    });
  });
});

class TestResource extends CfnResource {
  constructor(scope: Construct, id: string) {
    super(scope, id, {
      type: 'AWS::Test::Resource',
    });
  }
}

class DifferentTestResource extends CfnResource {
  constructor(scope: Construct, id: string) {
    super(scope, id, {
      type: 'AWS::Test::DifferentResource',
    });
  }
}

class ParentWithDefaultChild extends Construct {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    new CfnResource(this, 'ChildResource', {
      type: 'AWS::Test::ChildResource',
    });
  }
}

describe('addCfnGuardSuppressions', () => {
  test('adds suppressions to resource without default child', () => {
    const stack = new Stack();
    const resource = new TestResource(stack, 'TestResource');
    const suppressions = ['RULE_1', 'RULE_2'];

    addCfnGuardSuppressions(resource, suppressions);

    const template = Template.fromStack(stack);
    template.hasResource('AWS::Test::Resource', {
      Metadata: {
        guard: {
          SuppressedRules: suppressions,
        },
      },
    });
  });
});

describe('CfnGuardSuppressResourceList Error Cases', () => {
  test('handles empty suppression list', () => {
    const stack = new Stack();
    new TestResource(stack, 'TestResource');
    const suppressions = {
      'AWS::Test::Resource': [],
    };

    Aspects.of(stack).add(new CfnGuardSuppressResourceList(suppressions));

    const template = Template.fromStack(stack);
    template.hasResource('AWS::Test::Resource', {
      Metadata: {
        guard: {
          SuppressedRules: [],
        },
      },
    });
  });

  test('handles null default child', () => {
    class ConstructWithoutDefaultChild extends Construct {
      constructor(scope: Construct, id: string) {
        super(scope, id);
      }
    }

    const stack = new Stack();
    new ConstructWithoutDefaultChild(stack, 'TestConstruct');
    const suppressions = {
      'AWS::Test::Resource': ['RULE'],
    };

    expect(() => {
      Aspects.of(stack).add(new CfnGuardSuppressResourceList(suppressions));
    }).not.toThrow();
  });
});

describe('addCfnGuardSuppressions merge', () => {
  let mockResource: jest.Mocked<CfnResource>;

  beforeEach(() => {
    mockResource = {
      node: {
        defaultChild: null,
      },
      getMetadata: jest.fn(),
      addMetadata: jest.fn(),
    } as unknown as jest.Mocked<CfnResource>;
  });

  test('should merge new suppressions with existing ones and remove duplicates', () => {
    const existingMetadata = {
      SuppressedRules: ['rule1', 'rule2'],
      otherField: 'value'
    };
    mockResource.getMetadata.mockReturnValue(existingMetadata);

    addCfnGuardSuppressions(mockResource, ['rule2', 'rule3']);

    expect(mockResource.addMetadata).toHaveBeenCalledWith('guard', {
      SuppressedRules: ['rule1', 'rule2', 'rule3'],
      otherField: 'value'
    });
  });

  test('should handle case when no existing metadata is present', () => {
    mockResource.getMetadata.mockReturnValue(undefined);

    addCfnGuardSuppressions(mockResource, ['rule1', 'rule2']);

    expect(mockResource.addMetadata).toHaveBeenCalledWith('guard', {
      SuppressedRules: ['rule1', 'rule2']
    });
  });
});

