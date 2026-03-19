"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import {
  Controller,
  FormProvider,
  useFormContext,
  useFormState,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
} from "react-hook-form"

import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"

const Form = FormProvider

/* -------------------------------------------------------------------------- */
/*                               Form Context                                 */
/* -------------------------------------------------------------------------- */

type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> = {
  name: TName
}

const FormFieldContext =
  React.createContext<FormFieldContextValue>(
    {} as FormFieldContextValue
  )

/* -------------------------------------------------------------------------- */
/*                               Form Field                                   */
/* -------------------------------------------------------------------------- */

function FormField<
  TFieldValues extends FieldValues,
  TName extends FieldPath<TFieldValues>
>(props: ControllerProps<TFieldValues, TName>) {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  )
}

/* -------------------------------------------------------------------------- */
/*                               Form Item                                    */
/* -------------------------------------------------------------------------- */

type FormItemContextValue = {
  id: string
}

const FormItemContext =
  React.createContext<FormItemContextValue>(
    {} as FormItemContextValue
  )

function FormItem({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const id = React.useId()

  return (
    <FormItemContext.Provider value={{ id }}>
      <div
        data-slot="form-item"
        className={cn("grid gap-2", className)}
        {...props}
      />
    </FormItemContext.Provider>
  )
}

/* -------------------------------------------------------------------------- */
/*                              useFormField                                  */
/* -------------------------------------------------------------------------- */

function useFormField() {
  const fieldContext = React.useContext(FormFieldContext)
  const itemContext = React.useContext(FormItemContext)

  const { getFieldState } = useFormContext()
  const formState = useFormState({
    name: fieldContext.name,
  })

  const fieldState = getFieldState(
    fieldContext.name,
    formState
  )

  const { id } = itemContext

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  }
}

/* -------------------------------------------------------------------------- */
/*                                Label                                       */
/* -------------------------------------------------------------------------- */

function FormLabel({
  className,
  ...props
}: React.ComponentProps<typeof Label>) {
  const { error, formItemId } = useFormField()

  return (
    <Label
      data-slot="form-label"
      data-error={!!error}
      htmlFor={formItemId}
      className={cn(
        "data-[error=true]:text-destructive",
        className
      )}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/*                               Control                                      */
/* -------------------------------------------------------------------------- */

function FormControl(
  props: React.ComponentProps<typeof Slot>
) {
  const {
    error,
    formItemId,
    formDescriptionId,
    formMessageId,
  } = useFormField()

  return (
    <Slot
      data-slot="form-control"
      id={formItemId}
      aria-describedby={
        !error
          ? formDescriptionId
          : `${formDescriptionId} ${formMessageId}`
      }
      aria-invalid={!!error}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/*                            Description                                     */
/* -------------------------------------------------------------------------- */

function FormDescription({
  className,
  ...props
}: React.ComponentProps<"p">) {
  const { formDescriptionId } = useFormField()

  return (
    <p
      id={formDescriptionId}
      data-slot="form-description"
      className={cn(
        "text-muted-foreground text-sm",
        className
      )}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/*                               Message                                      */
/* -------------------------------------------------------------------------- */

function FormMessage({
  className,
  ...props
}: React.ComponentProps<"p">) {
  const { error, formMessageId } = useFormField()

  const body =
    error?.message?.toString() ?? props.children

  if (!body) return null

  return (
    <p
      id={formMessageId}
      data-slot="form-message"
      className={cn(
        "text-destructive text-sm",
        className
      )}
      {...props}
    >
      {body}
    </p>
  )
}

/* -------------------------------------------------------------------------- */

export {
  Form,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  FormField,
  useFormField,
}